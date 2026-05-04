# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .api_client import EskaerakApiClient

class estatistika_orokorrak(models.TransientModel):
    _name = 'estatistikak.estatistika_orokorrak'
    _description = 'Estatistika Orokorrak'

    name = fields.Char(string="Izena", default="Eskarien Estatistika Orokorrak")
    total_eskariak = fields.Integer(string="Eskariak guztira")
    total_zenbatekoa = fields.Float(string="Zenbatekoa guztira (eskariak)", digits=(16, 2))
    batez_besteko_zenbatekoa = fields.Float(string="Batez besteko zenbatekoa", digits=(16, 2))
    bezero_kopurua = fields.Integer(string="Mahai kopurua")

    @api.model
    def action_show_stats(self):
        record = self.create(self._get_estatistikak_values())
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'estatistikak.estatistika_orokorrak',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_show_graph(self):
        self.env['estatistikak.eskariak'].refresh_from_api()
        return self.env.ref('estatistikak.eskariak_action_graph').read()[0]

    @api.model
    def _get_estatistikak_values(self):
        eskariak = EskaerakApiClient(self.env).get_eskaerak_with_totals()
        total_eskariak = len(eskariak)
        total_zenbatekoa = sum(eskari.get('zenbatekoa', 0.0) for eskari in eskariak)
        mahaiak = {
            eskari.get('mahaiaId') or eskari.get('MahaiaId')
            for eskari in eskariak
            if eskari.get('mahaiaId') or eskari.get('MahaiaId')
        }
        return {
            'total_eskariak': total_eskariak,
            'total_zenbatekoa': total_zenbatekoa,
            'batez_besteko_zenbatekoa': total_zenbatekoa / total_eskariak if total_eskariak else 0.0,
            'bezero_kopurua': len(mahaiak),
        }
