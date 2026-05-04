# -*- coding: utf-8 -*-
import json
import logging
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EskaerakApiClient:
    """Small HTTP client for the restaurant API used by the statistics views."""

    DEFAULT_URLS = (
        'http://host.docker.internal:5005/api/eskaerak',
        'http://localhost:5005/api/eskaerak',
        'https://host.docker.internal:7236/api/eskaerak',
        'https://localhost:7236/api/eskaerak',
    )

    def __init__(self, env, timeout=10):
        self.env = env
        self.timeout = timeout
        self.ssl_context = ssl._create_unverified_context()

    def get_eskaerak_with_totals(self):
        api_url = self._configured_url()
        errors = []
        for url in self._candidate_urls(api_url):
            try:
                eskaerak = self._get_eskaerak(url)
                zerbitzua_totals = self._get_zerbitzua_totals(url, eskaerak)
                faktura_totals = self._get_faktura_totals(url)
                return [
                    dict(eskaera, zenbatekoa=self._get_total(url, eskaera, zerbitzua_totals, faktura_totals))
                    for eskaera in eskaerak
                ]
            except Exception as exc:
                _logger.info("Could not fetch eskaerak from %s: %s", url, exc)
                errors.append("%s: %s" % (url, exc))

        raise UserError(
            "Ezin izan dira eskaerak API-tik lortu.\n"
            "Begiratu APIa martxan dagoela eta Odoo-k URL hauetara sarbidea duela:\n%s"
            % "\n".join(errors)
        )

    def _configured_url(self):
        value = self.env['ir.config_parameter'].sudo().get_param('estatistikak.eskaerak_api_url')
        return (value or '').strip()

    def _candidate_urls(self, configured_url):
        urls = []
        if configured_url:
            urls.append(configured_url)
        urls.extend(url for url in self.DEFAULT_URLS if url not in urls)
        return urls

    def _get_eskaerak(self, api_url):
        payload = self._get_json(api_url)
        eskaerak = self._payload_items(payload)
        if not isinstance(eskaerak, list):
            raise UserError("APIaren erantzuna ez da eskaeren zerrenda bat.")
        return eskaerak

    def _get_zerbitzua_totals(self, api_url, eskaerak):
        totals = {}
        mahaia_ids = {
            self._field(eskaera, 'mahaiaId')
            for eskaera in eskaerak
            if self._field(eskaera, 'mahaiaId')
        }

        for mahaia_id in mahaia_ids:
            try:
                payload = self._get_json(self._zerbitzua_mahaia_url(api_url, mahaia_id))
            except Exception as exc:
                _logger.info("Could not fetch zerbitzua totals for mahaia %s: %s", mahaia_id, exc)
                continue

            zerbitzuak = self._payload_items(payload)
            if not isinstance(zerbitzuak, list):
                continue

            totals.update({
                self._field(zerbitzua, 'id'): self._float_field(zerbitzua, 'prezioTotala')
                for zerbitzua in zerbitzuak
                if self._field(zerbitzua, 'id')
            })

        return totals

    def _get_faktura_totals(self, api_url):
        try:
            payload = self._get_json(self._fakturak_url(api_url))
        except Exception as exc:
            _logger.info("Could not fetch fakturak totals: %s", exc)
            return {}

        fakturak = self._payload_items(payload)
        if not isinstance(fakturak, list):
            return {}

        return {
            self._field(faktura, 'zerbitzuaId'): self._float_field(faktura, 'prezioTotala')
            for faktura in fakturak
            if self._field(faktura, 'zerbitzuaId')
        }

    def _get_total(self, api_url, eskaera, zerbitzua_totals, faktura_totals):
        eskaera_id = self._field(eskaera, 'id')
        if eskaera_id in zerbitzua_totals:
            return zerbitzua_totals[eskaera_id]
        if eskaera_id in faktura_totals:
            return faktura_totals[eskaera_id]

        try:
            return self._get_eskaera_total_from_products(api_url, eskaera)
        except Exception as exc:
            _logger.info("Could not fetch products for eskaera %s: %s", eskaera_id, exc)
            return 0.0

    def _get_eskaera_total(self, api_url, eskaera):
        return self._get_eskaera_total_from_products(api_url, eskaera)

    def _get_eskaera_total_from_products(self, api_url, eskaera):
        eskaera_id = self._field(eskaera, 'id')
        if not eskaera_id:
            return 0.0

        produktuak_url = urljoin(api_url.rstrip('/') + '/', '%s/produktuak' % eskaera_id)
        payload = self._get_json(produktuak_url)
        produktuak = self._payload_items(payload)
        if not isinstance(produktuak, list):
            return 0.0

        total = 0.0
        for produktua in produktuak:
            prezioa = self._float_field(produktua, 'prezioUnitarioa')
            kantitatea = self._float_field(produktua, 'kantitatea')
            total += prezioa * kantitatea
        return total

    def _get_json(self, url):
        request = Request(url, headers={'Accept': 'application/json'})
        try:
            with urlopen(request, timeout=self.timeout, context=self.ssl_context) as response:
                return json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            raise UserError("APIak HTTP %s itzuli du." % exc.code)
        except URLError as exc:
            raise UserError("Ezin da APIra konektatu: %s" % exc.reason)
        except json.JSONDecodeError:
            raise UserError("APIaren erantzuna ez da JSON balioduna.")

    def _payload_items(self, payload):
        if isinstance(payload, dict):
            return payload.get('datuak') or payload.get('Datuak') or []
        return payload

    def _field(self, data, name, default=None):
        if not isinstance(data, dict):
            return default
        return data.get(name, data.get(name[:1].upper() + name[1:], default))

    def _float_field(self, data, name):
        value = self._field(data, name, 0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _fakturak_url(self, api_url):
        marker = '/api/eskaerak'
        if marker in api_url:
            return api_url.split(marker, 1)[0] + '/api/fakturak'
        return urljoin(api_url.rstrip('/') + '/', '../fakturak')

    def _zerbitzua_mahaia_url(self, api_url, mahaia_id):
        marker = '/api/eskaerak'
        if marker in api_url:
            return api_url.split(marker, 1)[0] + '/api/Zerbitzua/mahaia/%s' % mahaia_id
        return urljoin(api_url.rstrip('/') + '/', '../Zerbitzua/mahaia/%s' % mahaia_id)
