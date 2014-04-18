# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account analytic required module for OpenERP
#    Copyright (C) 2011 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    Developped during the Akretion-Camptocamp code sprint of June 2011
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _


class account_account_type(orm.Model):
    _inherit = "account.account.type"

    _columns = {
        'analytic_policy': fields.selection([
            ('optional', 'Optional'),
            ('always', 'Always'),
            ('never', 'Never')
            ], 'Policy for analytic account',
            help="Set the policy for analytic accounts : if you select "
            "'Optional', the accountant is free to put an analytic account "
            "on an account move line with this type of account ; if you "
            "select 'Always', the accountant will get an error message if "
            "there is no analytic account ; if you select 'Never', the "
            "accountant will get an error message if an analytic account "
            "is present."),
    }

    _defaults = {
        'analytic_policy': 'optional',
        }


class account_move_line(orm.Model):
    _inherit = "account.move.line"

    def check_analytic_required(self, cr, uid, ids, vals, context=None):
        if 'account_id' in vals or 'analytic_account_id' in vals or \
                'debit' in vals or 'credit' in vals:
            if isinstance(ids, (int, long)):
                ids = [ids]
            for move_line in self.browse(cr, uid, ids, context):
                if move_line.debit == 0 and move_line.credit == 0:
                    continue
                analytic_policy = \
                    move_line.account_id.user_type.analytic_policy
                if analytic_policy == 'always' and \
                        not move_line.analytic_account_id:
                    raise orm.except_orm(
                        _('Error :'),
                        _("Analytic policy is set to 'Always' with account "
                            "%s '%s' but the analytic account is missing in "
                            "the account move line with label '%s'.")
                        % (
                            move_line.account_id.code,
                            move_line.account_id.name,
                            move_line.name))
                elif analytic_policy == 'never' and \
                        move_line.analytic_account_id:
                    raise orm.except_orm(
                        _('Error :'),
                        _("Analytic policy is set to 'Never' with account %s "
                            "'%s' but the account move line with label '%s' "
                            "has an analytic account %s '%s'.")
                        % (
                            move_line.account_id.code,
                            move_line.account_id.name,
                            move_line.name,
                            move_line.analytic_account_id.code,
                            move_line.analytic_account_id.name))
        return True

    def create(self, cr, uid, vals, context=None, check=True):
        line_id = super(account_move_line, self).create(
            cr, uid, vals, context=context, check=check)
        self.check_analytic_required(cr, uid, line_id, vals, context=context)
        return line_id

    def write(
            self, cr, uid, ids, vals, context=None, check=True,
            update_check=True):
        res = super(account_move_line, self).write(
            cr, uid, ids, vals, context=context, check=check,
            update_check=update_check)
        self.check_analytic_required(cr, uid, ids, vals, context=context)
        return res
