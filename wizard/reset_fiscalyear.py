# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
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


class reset_fiscalyear(orm.TransientModel):
    _name = "reset.fiscalyear"
    _description = "Reset Fiscal Year"

    _columns = {
        'name': fields.char('Reference', size=64),
        'journal_id': fields.many2one(
            'account.journal',
            'Journal',
            required=True),
        'fiscalyear_id': fields.many2one(
            'account.fiscalyear',
            'Fiscal year',
            required=True),
        'force_validate': fields.boolean(
            'Force validate',
            help="If checked, it will validate all draft journal entries."),
        'close_fiscalyear': fields.boolean(
            'Close fiscalyear',
            help="If checked, it will close the previous fiscalyears."),
        }

    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        fiscalyear_id = False
        if context.get('active_id', False):
            fiscalyear_id = context['active_id']
        return fiscalyear_id

    _defaults = {
        'fiscalyear_id': _get_fiscalyear,
        }

    def reset_fiscalyear(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Reset fiscalyear may only be done one at a time.'
        wizard = self.browse(cr, uid, ids[0], context=context)
        if wizard.fiscalyear_id.state == 'closed':
            raise orm.except_orm(
                _('User Error'),
                _("You cannot reset a closed fiscalyear."))
        self.pool['account.fiscalyear']._reset_fiscalyear(
            cr, uid, wizard.fiscalyear_id, wizard.journal_id.id, wizard.name,
            force_validate=wizard.force_validate,
            close_fiscalyear=wizard.close_fiscalyear, context=context)
        return True

