# -*- coding: utf-8 -*-
###############################################################################
#
#   custom_account for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com). All Rights Reserved
#   @author Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import fields, orm
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class account_fiscalyear(orm.Model):
    _inherit = "account.fiscalyear"


    def close_fiscalyear(self, cr, uid, ids, context=None):
        for fy_id in ids:
            cr.execute("""
                UPDATE account_journal_period
                SET state = %s
                WHERE period_id IN
                    (SELECT id FROM account_period WHERE fiscalyear_id = %s)
                """, ('done', fy_id))
            cr.execute("""
                UPDATE account_period SET state = %s WHERE fiscalyear_id = %s
                """, ('done', fy_id))
            cr.execute("""
                UPDATE account_fiscalyear
                SET state = %s WHERE id = %s
                """, ('done', fy_id))
        return True

    def _check_previous_moves(
            self, cr, uid, date, force_validate=False, context=None):
        move_obj = self.pool['account.move']
        move_ids = move_obj.search(
            cr, uid, [('state', '=', 'draft'), ('date', '<=', date)],
            context=context)
        if move_ids and force_validate:
            # validate all draft account moves
            move_obj.button_validate(cr, uid, move_ids, context=context)
        elif move_ids:
            raise orm.except_orm(
                _('User error'),
                _("All previous journal entries must be validated, "
                  "or check 'Force validate'."))
        move_ids = move_obj.search(
            cr, uid, [('state', '=', 'draft'), ('date', '<=', date)],
            context=context)
        if move_ids:
            raise orm.except_orm(
                _('User error'),
                _("Some previous journal entries could not be validated, "
                  "check them before reseting the fiscalyear."))
        return True

    def _reset_fiscalyear(
            self, cr, uid, fiscalyear, journal_id, name, force_validate=False,
            close_fiscalyear=False, context=None):
        account_obj = self.pool['account.account']
        line_obj = self.pool['account.move.line']
        period_obj = self.pool['account.period']
        move_obj = self.pool['account.move']
        reconcile_obj = self.pool['account.move.reconcile']
        if context is None:
            context = {}
        _logger.info('Start reset fiscal year')
        #avoid write off
        context['fy_closing'] = True
        context['no_fields_compute'] = True
        context['no_move_check'] = True
        period_id = period_obj.find(cr, uid, fiscalyear.date_stop,
                                    context=context)[0]
        self._check_previous_moves(
            cr, uid, fiscalyear.date_stop, force_validate=force_validate,
            context=context)
        cr.execute("""
            SELECT reconcile_id
                FROM account_move_line
                WHERE reconcile_id is not NULL
                GROUP BY reconcile_id
                HAVING min(date) <= %s and max(date) > %s
        """, (fiscalyear.date_stop, fiscalyear.date_stop))
        reconcile_ids = cr.fetchall()
        reconcile_ids = [x[0] for x in reconcile_ids]
        reconcile_obj.unlink(cr, uid, reconcile_ids, context=context)
        move_vals = {
            'ref': name,
            'journal_id': journal_id,
            'period_id': period_id,
            'date': fiscalyear.date_stop,
            }
        cr.execute("""
            SELECT account_id, partner_id, sum(debit - credit)
                FROM account_move_line
                WHERE date <= %s
                GROUP BY account_id, partner_id
        """, (fiscalyear.date_stop,))
        balances = cr.dictfetchall()
        total_account = len(balances)
        current = 0
        lines = []
        for balance in balances:
            current += 1
            line_vals = {
                'name': name,
                'account_id': balance['account_id'],
                'journal_id': journal_id,
                'partner_id': balance['partner_id'] and balance['partner_id'] or False,
                'period_id': period_id,
                'date': fiscalyear.date_stop,
                }
            if balance['sum'] > 0:
                line_vals['credit'] = balance['sum']
            else:
                line_vals['debit'] = - balance['sum']
            lines.append((0, 0, line_vals))
            _logger.info(
                'Create balance move line: %s/%s',
                current, total_account)
        move_vals['line_id'] = lines
        _logger.info('Create balance move')
        move_id = move_obj.create(cr, uid, move_vals, context=context)
        _logger.info('Validate balance move')
        move_obj.button_validate(cr, uid, [move_id], context=context)
        move = move_obj.browse(cr, uid, move_id, context=context)
        total_reconcile = len(move.line_id)
        current = 0
        error = []
        for line in move.line_id:
            current += 1
            if not line.account_id.reconcile:
                continue
            if line.partner_id:
                reconcile_line_ids = line_obj.search(
                    cr, uid,
                    [('reconcile_id', '=', False),
                     ('id', '!=', line.id),
                     ('date', '<=', fiscalyear.date_stop),
                     ('account_id', '=', line.account_id.id),
                     ('partner_id', '=', line.partner_id.id)], context=context)
            else:
                reconcile_line_ids = line_obj.search(
                    cr, uid,
                    [('reconcile_id', '=', False),
                     ('id', '!=', line.id),
                     ('date', '<=', fiscalyear.date_stop),
                     ('account_id', '=', line.account_id.id),
                     ('partner_id', '=', False)], context=context)
            _logger.info(
                'Reconcile %s move lines : %s/%s',
                len(reconcile_line_ids), current, total_account)
            if reconcile_line_ids:
                reconcile_line_ids.append(line.id)
                try:
                    line_obj.reconcile(
                        cr, uid, reconcile_line_ids, context=context)
                except Exception, e:
                    error.append({e: reconcile_line_ids})
        if close_fiscalyear:
            _logger.info('Close fiscal year')
            fiscalyear_ids = self.search(
                cr, uid,
                [('date_stop', '<=', fiscalyear.date_stop),
                 ('state', '=', 'draft')],
                context=context)
            self.close_fiscalyear(cr, uid, fiscalyear_ids, context=context)
        _logger.info('End reset fiscal year')
        return True


class account_move_line(orm.Model):
    _inherit = "account.move.line"

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        """ Override the write of set check = False otherwise reconcile takes too much time."""
        if context is None:
            context = {}
        if context.get('no_move_check') or context.get('no_store_function'):
            check = False
        return super(account_move_line, self).write(
            cr, uid, ids, vals, context=context, check=check,
            update_check=update_check)


class account_invoice(orm.Model):
    _inherit = "account.invoice"

    def _store_set_values(self, cr, uid, ids, fields, context):
        if context is None:
           context = {}
        if context.get('no_fields_compute') or context.get('no_store_function'):
            return True
        return super(account_invoice, self)._store_set_values(cr, uid, ids, fields, context)
