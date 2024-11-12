from collections import OrderedDict

from django import forms
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from pretix.base.forms import SecretKeySettingsField
from pretix.base.signals import register_payment_providers, register_global_settings


@receiver(register_payment_providers, dispatch_uid="payment_orange_money_mdg")
def register_payment_provider(sender, **kwargs):
    from .payment import OrangeMoneyMadagascar

    return OrangeMoneyMadagascar


@receiver(
    register_global_settings, dispatch_uid="payment_orange_money_mdg_global_settings"
)
def register_global_settings(sender, **kwargs):
    return OrderedDict(
        [
            (
                "payment_orange_money_mdg_merchant_key",
                SecretKeySettingsField(
                    label=_("Orange Money Madagascar: Merchant Key"),
                    required=True,
                ),
            ),
            (
                "payment_orange_money_mdg_consumer_key",
                SecretKeySettingsField(
                    label=_("Orange Money Madagascar: Consumer key"),
                    required=True,
                ),
            ),
            (
                "payment_orange_money_mdg_client_id",
                forms.CharField(
                    label=_("Orange Money Madagascar: Client ID"),
                    required=True,
                ),
            ),
            (
                "payment_orange_money_mdg_client_secret",
                SecretKeySettingsField(
                    label=_("Orange Money Madagascar: Client secret"), required=True
                ),
            ),
            (
                "payment_orange_money_mdg_endpoint",
                forms.ChoiceField(
                    label=_("Orange Money Madagascar: Endpoint"),
                    initial="live",
                    choices=(
                        ("sandbox", "Sandbox"),
                        ("live", "Live"),
                    ),
                ),
            ),
        ]
    )
