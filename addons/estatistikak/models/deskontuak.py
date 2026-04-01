from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class deskontuak(models.Model):
    _name = 'estatistikak.deskontuak'
    _description = 'Deskontuak'

    name = fields.Char(required=True)
    deskontu_mota = fields.Selection([
        ('ehuneko', 'Ehuneko'),
        ('kopurua', 'Kopuru fijoa'),
    ], required=True, default="ehuneko")

    balioa = fields.Float(required=True)
    aktibo = fields.Boolean(default=True)

    hasiera_data = fields.Date(required=True)
    amaiera_data = fields.Date(required=True)

    @api.constrains('balioa')
    def _balioa_konprobatu(self):
        for rec in self:
            if rec.deskontu_mota == 'ehuneko' and not (0 <= rec.balioa <= 100):
                raise ValidationError("Ehuneko deskontuak 0 eta 100 artean izan behar du.")
            
    def deskontua_aktibatu(self, prezioa):
        """Behin deskontua aplikatuta, prezioa itzultzen du"""
        if self.deskontu_mota == 'ehuneko':
            return prezioa * (1 - self.balioa / 100)
        else:
            return max(prezioa - self.balioa, 0)
