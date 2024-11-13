import requests
import time
from collections import OrderedDict
from django.http import HttpRequest
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _
from pretix.base.models import Event
from pretix.base.payment import BasePaymentProvider, OrderPayment
from pretix.base.settings import SettingsSandbox
from pretix.multidomain.urlreverse import build_absolute_uri

from pretix_orange_money_mdg.models import ReferencedOrangeMoneyObject


class OrangeMoneyMadagascar(BasePaymentProvider):
    identifier = "orange_money_madagascar"
    verbose_name = _("Orange Money Madagascar")
    payment_form_fields = OrderedDict([])
    base_url = "https://api.orange.com/"
    url_prefix = ""
    execute_payment_needs_user = True
    test_mode_message = _(
        "No real money will be used for testing. You can check https://developer.orange.com/apis/om-webpay-dev/getting-started for more details on test payments."
    )

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox("payment", "orange_money_mdg", event)

    def init_api(self, request: HttpRequest):
        self.url_prefix = (
            ""
            if self.settings.endpoint == "live"
            else "/orange-money-webpay/dev/v1/webpayment"
        )
        self.get_access_token()

    def get_access_token(self):
        data = {
            "grant_type": "client_credentials",
        }
        headers = {
            "Authorization": f"Basic {self.settings.consumer_key}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        response = requests.post(
            self.base_url + "/oauth/v3/token", headers=headers, data=data
        )
        response_json = response.json()
        self.access_token = response_json["access_token"]

    def checkout_prepare(self, request, cart):
        self.init_api(request)
        if self.access_token:
            self.prepare_payment(cart, request)
            if request.session.get("orange_money_mdg_payment_url"):
                return True
        return False

    def prepare_payment(self, cart, request):
        data = {
            "merchant_key": self.settings.merchant_key,
            "currency": "OUV"
            if self.settings.endpoint == "sandbox"
            else self.event.currency,
            "order_id": f"order_{get_random_string(length=25)}_{time.time()}",
            "amount": float(cart["total"]),
            "notif_url": build_absolute_uri(
                request.event, "plugins:pretix_orange_money_mdg:notify", kwargs={}
            ),
            "return_url": build_absolute_uri(
                request.event, "plugins:pretix_orange_money_mdg:success", kwargs={}
            ),
            "cancel_url": build_absolute_uri(
                request.event, "plugins:pretix_orange_money_mdg:abort", kwargs={}
            ),
            "lang": request.LANGUAGE_CODE.split("-")[0],
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = requests.post(
            self.base_url + self.url_prefix, headers=headers, json=data
        )
        response_json = response.json()
        if response_json["message"] == "OK":
            request.session["orange_money_mdg_payment_url"] = response_json[
                "payment_url"
            ]
            request.session["orange_money_mdg_notif_token"] = response_json[
                "notif_token"
            ]

    def checkout_confirm_render(self, request):
        return _("You will be redirected to Orange Money website")

    def payment_is_valid_session(self, request):
        return True

    def execute_payment(self, request: HttpRequest, payment: OrderPayment):
        # This will be used to find the payment on notify
        reference = ReferencedOrangeMoneyObject(
            payment=payment,
            reference=request.session["orange_money_mdg_notif_token"],
            order=payment.order,
        )
        reference.save()
        return request.session.get("orange_money_mdg_payment_url") or ""
