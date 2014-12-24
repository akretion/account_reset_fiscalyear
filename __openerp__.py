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



{
    'name': 'account_reset_fiscalyear',
    'version': '0.1',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'description': """
    This module reset a previous fiscalyear in order to clean accounting to
    prepare the new fiscalyear.
    It validates automaticaly the draft account_move and create an account move
    that resets each account to zero.
    """,
    'author': 'Akretion',
    'website': 'http://www.akretion.com/',
    'depends': ['account'],
    'data': [
        'wizard/reset_fiscalyear_view.xml',
        'account_view.xml',
    ],
    'demo': [],
    'installable': True,
}

