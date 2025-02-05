# coding: utf-8
import logging
import hmac
import hashlib
import base64
import uuid

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.addons.payment_bac.controllers.payment import BACController
from odoo.tools.float_utils import float_compare
from odoo.http import request

_logger = logging.getLogger(__name__)

signed_field_names = ['access_key', 'profile_id', 'transaction_uuid', 'signed_field_names', 'unsigned_field_names', 'signed_date_time', 'locale', 'transaction_type', 'reference_number', 'amount', 'currency', 'ship_to_address_city']

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'bac':
            return res
        
        return_url = urls.url_join(self.provider_id.get_base_url(), BACController._return_url)
        reference = self.reference
        bac_partner_address1 = self.partner_id.street[0:35] if self.partner_id.street else ''
        bac_partner_address2 = self.partner_id.street2[0:35] if self.partner_id.street2 else ''
        
        to_hash = 'process_fixed|'+str(processing_values['amount'])+'|'+reference+'|'+self.provider_id.bac_key_text
        m = hashlib.md5(to_hash.encode('utf-8'))
        
        rendering_values = {
            'api_url': self.provider_id._bac_get_api_url(),
            'bac_key_id': self.provider_id.bac_key_id,
            'bac_key_text': self.provider_id.bac_key_text,
            'bac_amount': processing_values['amount'],
            'bac_reference': reference,
            'bac_return': return_url,
            'bac_hash': 'action|amount|order_description|'+m.hexdigest(),
            'bac_partner_first_name': self.partner_id.name,
            'bac_partner_last_name': '',
            'bac_partner_email': self.partner_id.email,
            'bac_partner_postal_code': self.partner_id.zip,
            'bac_partner_city': self.partner_id.city,
            'bac_partner_state': self.partner_id.state_id.code,
            'bac_partner_country': self.partner_id.country_id.code,
            'bac_partner_phone': self.partner_id.phone,
            'bac_partner_address1': bac_partner_address1,
            'bac_partner_address2': bac_partner_address2,
        }
        return rendering_values

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'bac':
            return tx
        
        reference = notification_data.get('order_description', '')
        if not reference:
            error_msg = _('BAC: received data with missing reference (%s)') % (reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'bac')])
        _logger.info(tx)

        if not tx or len(tx) > 1:
            error_msg = _('BAC: received data for reference %s') % (reference)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple orders found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'bac':
            return
        
        reference = notification_data.get('order_description', '')
        
        self.provider_reference = reference
        status_code = notification_data.get('response', '3')
        if status_code == '1':
            self._set_done()
        else:
            error = 'BAC: error '+notification_data.get('message')
            _logger.info(error)
            self._set_error(_("Your payment was refused (code %s). Please try again.", status_code))
