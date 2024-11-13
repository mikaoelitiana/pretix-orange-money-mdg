import logging
import json

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django_scopes import scopes_disabled

from pretix.base.models import (
    Order,
)
from pretix.multidomain.urlreverse import eventreverse

from pretix_orange_money_mdg.models import ReferencedOrangeMoneyObject

logger = logging.getLogger("pretix.plugins.paypal2")


@csrf_exempt
@require_POST
@scopes_disabled()
def notify(request, *args, **kwargs):
    # OrangeMoney notify us when a payment succeds
    # cf. https://developer.orange.com/apis/om-webpay-dev/getting-started#33-transaction-notification
    # The body object looks like this :
    # {
    #    "status":"SUCCESS",
    #    "notif_token":"dd497bda3b250e536186fc0663f32f40",
    #    "txnid": "MP150709.1341.A00073"
    # }
    payload = json.loads(request.body)
    # Try to find the payment from a given notif_token
    reference = ReferencedOrangeMoneyObject.objects.get(
        reference=payload["notif_token"]
    )
    # If payment is found, confirm it
    if reference.payment:
        reference.payment.confirm()
        return HttpResponse(f"Payment for order {reference.payment.order} confirmed.")
    return HttpResponse("Payment not found", status=404)


def success(request, *args, **kwargs):
    # From the stored notif_token value in the session, look for the reference object
    # and the related payment
    if request.session.get("orange_money_mdg_notif_token"):
        reference = ReferencedOrangeMoneyObject.objects.get(
            reference=request.session.get("orange_money_mdg_notif_token")
        )
        payment = reference.payment
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
        return redirect(
            eventreverse(
                request.event,
                "presale:event.order",
                kwargs={},
            )
        )


def abort(request, *args, **kwargs):
    messages.error(request, _("It looks like you canceled the OrangeMoney payment"))
