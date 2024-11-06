from django.dispatch import receiver

from pretix.base.signals import register_payment_providers

@receiver(register_payment_providers, dispatch_uid="payment_orange_money_mdg")
def register_payment_provider(sender, **kwargs):
    from .payment import OrangeMoneyMadagascar
    return OrangeMoneyMadagascar
