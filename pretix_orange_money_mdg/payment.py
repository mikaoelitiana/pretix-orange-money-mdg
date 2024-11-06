from collections import OrderedDict

from django import forms
from django.utils.translation import gettext as __, gettext_lazy as _

from pretix.base.models import Event
from pretix.base.payment import BasePaymentProvider
from pretix.base.settings import SettingsSandbox

class OrangeMoneyMadagascar(BasePaymentProvider) :
    identifier = 'orange_money_madagascar'
    verbose_name = _('Orange Money Madagascar')
    payment_form_fields = OrderedDict([
    ])

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox('payment', 'orange_money_madagascar', event)

