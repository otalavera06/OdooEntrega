# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .api_client import EskaerakApiClient

class eskariak(models.Model):
    _name = 'estatistikak.eskariak'
    _description = 'Eskarien API Cachea'

    name = fields.Char(string="Eskari Zenbakia", required=True)
    data = fields.Date(string="Data", default=fields.Date.today, required=True)
    day_of_month = fields.Integer(string="Hilabeteko Eguna", compute="_compute_day_of_month", store=True)
    bezeroa = fields.Char(string="Mahaia")
    zenbatekoa = fields.Float(string="Zenbatekoa")

    @api.model
    def refresh_from_api(self):
        eskaerak = EskaerakApiClient(self.env).get_eskaerak_with_totals()
        self.search([]).unlink()

        for eskaera in eskaerak:
            eskaera_id = eskaera.get('id') or eskaera.get('Id')
            mahaia_id = eskaera.get('mahaiaId') or eskaera.get('MahaiaId')
            self.create({
                'name': eskaera.get('izena') or eskaera.get('Izena') or 'Eskaera #%s' % eskaera_id,
                'data': self._api_date(eskaera.get('data') or eskaera.get('Data')),
                'bezeroa': 'Mahaia %s' % mahaia_id if mahaia_id else '',
                'zenbatekoa': eskaera.get('zenbatekoa') or 0.0,
            })

    @api.depends('data')
    def _compute_day_of_month(self):
        for rec in self:
            if rec.data:
                rec.day_of_month = rec.data.day
            else:
                rec.day_of_month = 0

    @api.model
    def _api_date(self, value):
        if not value:
            return fields.Date.today()
        return str(value).split('T', 1)[0].split(' ', 1)[0]
