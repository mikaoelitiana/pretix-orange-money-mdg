import logging
import json
from pprint import pprint

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django_scopes import scopes_disabled

from pretix.base.models import (
    Order,
    OrderPayment,
)
from pretix.multidomain.urlreverse import eventreverse

logger = logging.getLogger("pretix.plugins.paypal2")


@csrf_exempt
@require_POST
@scopes_disabled()
def notify(request, *args, **kwargs):
    payload = json.loads(request.body)
    return HttpResponse(f"Payment {payload.status}")


def success(request, *args, **kwargs):
    pprint(request.session)
    if request.session.get("payment_paypal_payment"):
        payment = OrderPayment.objects.get(
            pk=request.session.get("payment_paypal_payment")
        )
    else:
        payment = None

    if payment:
        return redirect(
            eventreverse(
                request.event,
                "presale:event.order",
                kwargs={"order": payment.order.code, "secret": payment.order.secret},
            )
            + ("?paid=yes" if payment.order.status == Order.STATUS_PAID else "")
        )
    else:
        return False


def abort(request, *args, **kwargs):
    messages.error(request, _("It looks like you canceled the OrangeMoney payment"))