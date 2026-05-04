# -*- coding: utf-8 -*-
import json
import logging
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LangileakApiClient:
    DEFAULT_URLS = (
        'https://host.docker.internal:7236/api/langileak',
        'https://localhost:7236/api/langileak',
        'http://host.docker.internal:5005/api/langileak',
        'http://localhost:5005/api/langileak',
    )

    def __init__(self, env, timeout=10):
        self.env = env
        self.timeout = timeout
        self.ssl_context = ssl._create_unverified_context()

    def get_langileak(self):
        configured_url = self._configured_url()
        errors = []
        for url in self._candidate_urls(configured_url):
            try:
                langileak = self._payload_items(self._get_json(url))
                if not isinstance(langileak, list):
                    raise UserError("APIaren erantzuna ez da langileen zerrenda bat.")
                return langileak
            except Exception as exc:
                _logger.info("Could not fetch langileak from %s: %s", url, exc)
                errors.append("%s: %s" % (url, exc))

        raise UserError(
            "Ezin izan dira langileak API-tik lortu.\n"
            "Begiratu APIa martxan dagoela eta Odoo-k URL hauetara sarbidea duela:\n%s"
            % "\n".join(errors)
        )

    def _configured_url(self):
        value = self.env['ir.config_parameter'].sudo().get_param('langileak_api.langileak_api_url')
        return (value or '').strip()

    def _candidate_urls(self, configured_url):
        urls = []
        if configured_url:
            urls.append(configured_url)
        urls.extend(url for url in self.DEFAULT_URLS if url not in urls)
        return urls

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
