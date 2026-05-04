# -*- coding: utf-8 -*-
from odoo import fields, models

from .api_client import LangileakApiClient


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    langileak_api_id = fields.Integer(string="API Langile ID", copy=False, index=True)
    langileak_api_erabiltzailea = fields.Char(string="API Erabiltzailea", copy=False)
    langileak_api_chat_baimena = fields.Boolean(string="Txat baimena", copy=False)
    langileak_api_admin_baimena = fields.Boolean(string="Admin baimena", copy=False)
    langileak_api_mahaia_id = fields.Integer(string="API Mahaia ID", copy=False)

    def sync_langileak_from_api(self):
        langileak = LangileakApiClient(self.env).get_langileak()
        Employee = self.env['hr.employee'].sudo()

        for langilea in langileak:
            langilea_id = langilea.get('id') or langilea.get('Id')
            if not langilea_id:
                continue

            values = self._langilea_values(langilea)
            employee = Employee.search([('langileak_api_id', '=', langilea_id)], limit=1)
            if employee:
                employee.write(values)
            else:
                values['langileak_api_id'] = langilea_id
                Employee.create(values)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Langileak sinkronizatuta',
                'message': '%s langile ekarri dira API-tik.' % len(langileak),
                'type': 'success',
                'sticky': False,
            },
        }

    def _langilea_values(self, langilea):
        izena = langilea.get('izena') or langilea.get('Izena') or ''
        abizena = langilea.get('abizena') or langilea.get('Abizena') or ''
        erabiltzailea = langilea.get('erabiltzailea') or langilea.get('Erabiltzailea') or ''
        email = langilea.get('email') or langilea.get('Email') or ''
        telefonoa = langilea.get('telefonoa') or langilea.get('Telefonoa') or ''

        name = ("%s %s" % (izena, abizena)).strip() or erabiltzailea or email or "Langilea"
        return {
            'name': name,
            'work_email': email,
            'work_phone': telefonoa,
            'job_title': 'Langilea',
            'department_id': self._default_department().id,
            'langileak_api_erabiltzailea': erabiltzailea,
            'langileak_api_chat_baimena': self._bool_field(langilea, 'chatBaimena'),
            'langileak_api_admin_baimena': self._bool_field(langilea, 'baimena'),
            'langileak_api_mahaia_id': langilea.get('mahaiakId') or langilea.get('MahaiakId') or 0,
        }

    def _default_department(self):
        Department = self.env['hr.department'].sudo()
        return (
            Department.search([('name', '=', 'Administración')], limit=1)
            or Department.search([('name', '=', 'Administration')], limit=1)
            or Department.create({'name': 'Administración'})
        )

    def _bool_field(self, data, name):
        value = data.get(name) or data.get(name[:1].upper() + name[1:])
        return bool(value)
