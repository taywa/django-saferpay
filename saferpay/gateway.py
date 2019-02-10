import requests
import logging
import time
import uuid
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.translation import ugettext as _
from . models import SaferpayTransaction, SaferpayResponse
from . execptions import PaymentError, TransactionDeclined, GatewayError, UnableToTakePayment
logger = logging.getLogger('saferpay.saferpay')

API_PATHS = dict(
    PAYMENTPAGE_INIT='/Payment/v1/PaymentPage/Initialize',
    PAYMENTPAGE_ASSERT='/Payment/v1/PaymentPage/Assert',
    TRANSACTION_CAPTURE='/Payment/v1/Transaction/Capture',
    TRANSACTION_CANCEL='/Payment/v1/Transaction/Cancel'
)
API_PATHS_LOOKUP = {v: k for k, v in API_PATHS.items()}
SPECVERSION = 1.9


class SaferpayService:
    def __init__(self, order_id=None, notify_token='', amount=None, currency=None,
                 language_code='en', token=None, sp_trans=None):
        self.order_id, self.amount, self.currency = (
            order_id, amount, currency
        )
        self.language_code = language_code
        self.FORCE_LIABILITY_SHIFT_ACTIVE = getattr(
            settings, 'SAFERPAY_FORCE_LIABILITYSHIFT_ACTIVE', False
        )
        self.DO_NOTIFY = getattr(
            settings, 'SAFERPAY_DO_NOTIFY', False
        )
        self.ORDER_TEXT_NR = getattr(settings, 'SAFERPAY_ORDER_TEXT_NR', 'Order nr. %s')
        self.APIURL, self.CUSTOMERID, self.TERMINALID = (
            settings.SAFERPAY_APIURL, settings.SAFERPAY_CUSTOMERID,
            settings.SAFERPAY_TERMINALID
        )
        s = requests.Session()
        s.auth = (settings.SAFERPAY_USERNAME, settings.SAFERPAY_PASSWORD)
        self.SITE_BASE_URL = '{}://{}'.format(
            'https' if settings.USE_HTTPS else 'http',
            Site.objects.get_current().domain
        )
        self.SUCCESS_URL = '{}{}'.format(self.SITE_BASE_URL, settings.SAFERPAY_SUCCESS_URL)
        self.SUCCESS_CAPTURE_URL = '{}{}'.format(
            self.SITE_BASE_URL, settings.SAFERPAY_SUCCESS_CAPTURE_URL
        )
        self.FAIL_URL = '{}{}'.format(self.SITE_BASE_URL, settings.SAFERPAY_FAIL_URL)
        self._session = s
        self._next_url, self.sp_trans, self.token, self.notify_token = (
            None, sp_trans, token, notify_token
        )

    @classmethod
    def init_from_transaction(cls, token=None):
        sp_trans = SaferpayTransaction.objects.get(token=token)
        return cls(
            order_id=sp_trans.order_id, notify_token=sp_trans.notify_token, amount=sp_trans.amount,
            currency=sp_trans.currency, language_code=sp_trans.language_code,
            token=token, sp_trans=sp_trans
        )

    def _url(self, key):
        return "{base}{append}".format(base=self.APIURL, append=API_PATHS.get(key, ''))

    def _post(self, api_path, payload):
        start_time = time.time()
        res = self._session.post(self._url(api_path), json=payload)
        res_time = (time.time() - start_time) * 1000.0
        return res, res_time

    def _new_uuid_id(self):
        return str(uuid.uuid4())

    def _new_saferpay_response(
            self, api_path, payload, res, res_time, transaction, status_code=200):
        sp_res = SaferpayResponse(
            url=self._url(api_path),
            payload=payload, response=res.text,
            response_time=res_time, transaction=transaction, status_code=status_code
        )
        sp_res.save()

    def payload_init(self, billing_address):
        payload = {
            'RequestHeader': {
                'SpecVersion': SPECVERSION,
                'CustomerId': self.CUSTOMERID,
                'RequestId': self._new_uuid_id(),
                'RetryIndicator': 0
            },
            'TerminalId': self.TERMINALID,
            'Payment': {
                'Amount': {
                    'Value': int(self.amount * 100),
                    'CurrencyCode': self.currency
                },
                'OrderId': self.order_id,
                'BillingAddress': billing_address,
                'Description': self.ORDER_TEXT_NR % self.order_id,
            },
            "Payer": {
                'LanguageCode': self.language_code
            },
            'ReturnUrls': {
                'Success': self.SUCCESS_CAPTURE_URL,
                'Fail': self.FAIL_URL
            }
        }

        return payload

    def add_do_notify(self, payload, notify_token):
        notify_url = reverse('saferpay-notify', kwargs={'notify_token': notify_token})
        payload['Notification'] = {
            'NotifyUrl': f'{self.SITE_BASE_URL}{notify_url}'
        }
        return payload

    def paymentpage_init(self, payload):
        notify_token = self._new_uuid_id()
        if self.DO_NOTIFY:
            payload = self.add_do_notify(payload, notify_token)
        res, res_time = self._post('PAYMENTPAGE_INIT', payload)
        if res.status_code == 200 and 'RedirectUrl' in res.json():
            data = res.json()
            sp_trans = SaferpayTransaction(
                token=data['Token'], order_id=self.order_id, notify_token=notify_token,
                amount=self.amount, currency=self.currency, language_code=self.language_code
            )
            sp_trans.save()
            self._new_saferpay_response(
                'PAYMENTPAGE_INIT', payload, res, res_time, sp_trans, status_code=res.status_code
            )
            self._next_url = data['RedirectUrl']
            self.token = data['Token']
            return data['Token']
        elif res:
            raise GatewayError('PAYMENTPAGE_INIT failed')
        else:
            print(res.status_code, res.text)
            raise PaymentError('PAYMENTPAGE_INIT')

    def paymentpage_redirect(self):
        return redirect(self._next_url)

    def payload_assert(self):
        payload = {
            'RequestHeader': {
                'SpecVersion': SPECVERSION,
                'CustomerId': self.CUSTOMERID,
                'RequestId': self._new_uuid_id(),
                'RetryIndicator': 0
            },
            'Token': self.token
        }
        return payload

    def paymentpage_assert(self):
        payload = self.payload_assert()
        res, res_time = self._post('PAYMENTPAGE_ASSERT', payload)
        if res.status_code == 200 and 'Transaction' in res.json():
            res_data = res.json()
            self.sp_trans.transaction_id = res_data['Transaction']['Id']
            self.sp_trans.status = res_data['Transaction']['Status']
            self.sp_trans.save()
            self._new_saferpay_response(
                'PAYMENTPAGE_ASSERT', payload, res, res_time, self.sp_trans,
                status_code=res.status_code
            )
            if self.FORCE_LIABILITY_SHIFT_ACTIVE and 'Liability' in res_data \
               and res_data['Liability']['LiabilityShift'] is False:
                return self.transaction_cancel()
            if res_data['Transaction']['Status'] == 'AUTHORIZED':
                return self.transaction_capture()
            elif res_data['Transaction']['Status'] == 'CAPTURED':
                return 'CAPTURED'
        elif res:
            self._new_saferpay_response(
                'PAYMENTPAGE_ASSERT', payload, res, res_time, self.sp_trans,
                status_code=res.status_code
            )
            raise GatewayError('PAYMENTPAGE_ASSERT failed')
        else:
            raise PaymentError('PAYMENTPAGE_ASSERT')

    def payload_capture(self):
        payload = {
            'RequestHeader': {
                'SpecVersion': SPECVERSION,
                'CustomerId': self.CUSTOMERID,
                'RequestId': self._new_uuid_id(),
                'RetryIndicator': 0
            },
            "TransactionReference": {
                "TransactionId": self.sp_trans.transaction_id
            }
        }
        return payload

    def transaction_capture(self):
        payload = self.payload_capture()
        res, res_time = self._post('TRANSACTION_CAPTURE', payload)
        if res.status_code == 200 and 'Status' in res.json() \
           and res.json()['Status'] == 'CAPTURED':
            self.sp_trans.status = 'CAPTURED'
            self.sp_trans.save()
            self._new_saferpay_response(
                'TRANSACTION_CAPTURE', payload, res, res_time, self.sp_trans,
                status_code=res.status_code
            )
            return 'CAPTURED'
        elif res:
            self._new_saferpay_response(
                'PAYMENTPAGE_ASSERT', payload, res, res_time, self.sp_trans,
                status_code=res.status_code
            )
            self.transaction_cancel()
            raise UnableToTakePayment('TRANSACTION_CAPTURE failed')
        else:
            raise PaymentError('TRANSACTION_CAPTURE')

    def payload_cancel(self):
        payload = {
            'RequestHeader': {
                'SpecVersion': SPECVERSION,
                'CustomerId': self.CUSTOMERID,
                'RequestId': self._new_uuid_id(),
                'RetryIndicator': 0
            },
            'TransactionReference': {
                'TransactionId': self.sp_trans.transaction_id
            }
        }
        return payload

    def transaction_cancel(self):
        payload = self.payload_cancel()
        res, res_time = self._post('TRANSACTION_CANCEL', payload)
        if res.status_code == 200 and 'TransactionId' in res.json():
            self._new_saferpay_response(
                'TRANSACTION_CANCEL', payload, res, res_time, self.sp_trans,
                status_code=res.status_code
            )
            raise UnableToTakePayment('TRANSACTION_CANCEL')
        elif res:
            self._new_saferpay_response(
                'TRANSACTION_CANCEL', payload, res, res_time, self.sp_trans,
                status_code=res.status_code
            )
            raise UnableToTakePayment('TRANSACTION_CAPTURE failed')
        else:
            raise PaymentError('TRANSACTION_CAPTURE')
