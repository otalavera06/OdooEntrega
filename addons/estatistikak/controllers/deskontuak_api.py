from odoo import http
from odoo.http import request


class DeskontuakAPI(http.Controller):

    @http.route('/api/deskontuak', auth='public', methods=['GET'], type='json')
    def get_deskontu_guztiak(self):
        deskontuak = request.env['estatistikak.deskontuak'].sudo().search([])
        return [
            {
                'id': d.id,
                'name': d.name,
                'deskontu_mota': d.deskontu_mota,
                'balioa': d.balioa,
                'aktibo': d.aktibo,
            }
            for d in deskontuak
        ]
    
    @http.route('/api/deskontuak/jarri', auth='public', methods=['POST'], type='json')
    def deskontua_jarri(self, **kwargs):
        deskontua_id = kwargs.get('deskontua_id')
        prezioa = kwargs.get('prezioa')

        if not deskontua_id or prezioa is None:
            return {'error': 'deskontua_id eta prezioa beharrezkoak dira.'}
        
        deskontua = request.env['estatistikak.deskontuak'].sudo().browse(deskontua_id)

        if not deskontua.exists():
            return {'error': "Deskontua ez da aurkitu."}
        
        prezio_berria = deskontua.deskontua_aktibatu(prezioa)

        return {
            'prezio_originala': prezioa,
            'deskontatutako_prezioa': prezio_berria,
            'deskontua': deskontua.name,
        }
