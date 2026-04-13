# -*- coding: utf-8 -*-

from odoo import models, fields, api

class estatistika_orokorrak(models.TransientModel):
    _name = 'estatistikak.estatistika_orokorrak'
    _description = 'Estatistika Orokorrak'

    name = fields.Char(string="Estatistikaren Izena", default="Deskontuen Estatistika Orokorrak")
    
    total_deskontuak = fields.Integer(string="Deskontu kopurua", compute="_compute_estatistikak")
    aktibo_kopurua = fields.Integer(string="Deskontu aktiboak", compute="_compute_estatistikak")
    ehuneko_kopurua = fields.Integer(string="Ehuneko deskontuak", compute="_compute_estatistikak")
    finkoa_kopurua = fields.Integer(string="Kopuru finkoko deskontuak", compute="_compute_estatistikak")
    batez_besteko_balioa = fields.Float(string="Batez besteko balioa", compute="_compute_estatistikak")

    @api.model
    def action_show_stats(self):
        """Metodo honek estatistikak erakutsiko dituen bista irekitzen du"""
        record = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'estatistikak.estatistika_orokorrak',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _compute_estatistikak(self):
        for rec in self:
            deskontuak = self.env['estatistikak.deskontuak'].search([])
            rec.total_deskontuak = len(deskontuak)
            rec.aktibo_kopurua = len(deskontuak.filtered(lambda d: d.aktibo))
            rec.ehuneko_kopurua = len(deskontuak.filtered(lambda d: d.deskontu_mota == 'ehuneko'))
            rec.finkoa_kopurua = len(deskontuak.filtered(lambda d: d.deskontu_mota == 'kopurua'))
            
            if rec.total_deskontuak > 0:
                rec.batez_besteko_balioa = sum(deskontuak.mapped('balioa')) / rec.total_deskontuak
            else:
                rec.batez_besteko_balioa = 0.0
