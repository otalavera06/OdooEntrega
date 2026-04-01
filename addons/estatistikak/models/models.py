# -*- coding: utf-8 -*-

from odoo import models, fields, api


class estatistika_orokorrak(models.Model):
    _name = 'estatistikak.estatistika_orokorrak'
    _description = 'estatistikak.estatistika_orokorrak'

    name = fields.Char()

class estatistika_espezifikoak(models.Model):
    _name = 'estatistikak.estatistika_espezifikoak'
    _description = 'estatistikak.estatistika_espezifikoak'

    name = fields.Char()

