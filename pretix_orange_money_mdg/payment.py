from collections import OrderedDict

from pretix.base.payment import BasePaymentProvider

class OrangeMoneyMadagascar(BasePaymentProvider) :
    identifier = 'orange_money_madagascar'
    verbose_name = _('OrangeMoneyMadagascar')
    payment_form_fields = OrderedDict([
    ])

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox('payment', 'orange_money_madagascar', event)
