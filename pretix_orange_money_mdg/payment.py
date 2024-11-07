from collections import OrderedDict

import requests

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from pretix.base.models import Event
from pretix.base.payment import BasePaymentProvider
from pretix.base.settings import SettingsSandbox, global_settings_object

class OrangeMoneyMadagascar(BasePaymentProvider) :
    identifier = 'orange_money_madagascar'
    verbose_name = _('Orange Money Madagascar')
    payment_form_fields = OrderedDict([])
    base_url = "https://api.orange.com/"
    url_prefix = ""
    access_token = ""

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox('payment', 'orange_money_mdg', event)

    def init_api(self, request: HttpRequest):
        self.url_prefix = "" if self.settings.endpoint == "live" else "/orange-money-webpay/dev/v1/webpayment"
        data = {
            "grant_type": "client_credentials",
        }
        headers = {
            "Authorization": f"Basic {self.settings.consumer_key}" ,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        response = requests.post(self.base_url + '/oauth/v3/token', headers=headers, data=data)
        response_json = response.json()
        self.access_token = response_json["access_token"]

    def checkout_prepare(self, request, cart):
        self.init_api(request)
        if self.access_token:
            return True
        return False

