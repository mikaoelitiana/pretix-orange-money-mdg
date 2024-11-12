import logging

from django.contrib import messages
from django.core import signing
from django.http import (
    Http404,
    HttpResponseBadRequest,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import TemplateView

from pretix.base.models import (
    Order,
    OrderPayment,
)
from pretix.base.payment import PaymentException
from pretix.base.services.cart import add_payment_to_cart
from pretix.helpers.http import redirect_to_url
from pretix.multidomain.urlreverse import eventreverse
from pretix.plugins.paypal2.payment import (
    PaypalMethod as Paypal,
    PaypalWallet,
)
from pretix.presale.views.cart import cart_session

logger = logging.getLogger("pretix.plugins.paypal2")


class PaypalOrderView:
    def dispatch(self, request, *args, **kwargs):
        try:
            self.order = request.event.orders.get_with_secret_check(
                code=kwargs["order"],
                received_secret=kwargs["hash"].lower(),
                tag="plugins:paypal2:pay",
            )
        except Order.DoesNotExist:
            raise Http404("Unknown order")
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def payment(self):
        return get_object_or_404(
            self.order.payments,
            pk=self.kwargs["payment"],
            provider__istartswith="paypal",
        )

    def _redirect_to_order(self):
        return redirect(
            eventreverse(
                self.request.event,
                "presale:event.order",
                kwargs={"order": self.order.code, "secret": self.order.secret},
            )
            + ("?paid=yes" if self.order.status == Order.STATUS_PAID else "")
        )


@xframe_options_exempt
def redirect_view(request, *args, **kwargs):
    signer = signing.Signer(salt="safe-redirect")
    try:
        url = signer.unsign(request.GET.get("url", ""))
    except signing.BadSignature:
        return HttpResponseBadRequest("Invalid parameter")

    r = render(
        request,
        "pretixplugins/paypal2/redirect.html",
        {
            "url": url,
        },
    )
    r._csp_ignore = True
    return r


@method_decorator(xframe_options_exempt, "dispatch")
class PayView(PaypalOrderView, TemplateView):
    template_name = ""

    def dispatch(self, request, *args, **kwargs):
        self.request.pci_dss_payment_page = True
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.payment.state != OrderPayment.PAYMENT_STATE_CREATED:
            return self._redirect_to_order()
        else:
            r = render(
                request, "pretixplugins/paypal2/pay.html", self.get_context_data()
            )
            return r

    def post(self, request, *args, **kwargs):
        try:
            self.payment.payment_provider.execute_payment(request, self.payment)
        except PaymentException as e:
            messages.error(request, str(e))
        return self._redirect_to_order()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["order"] = self.order
        ctx["oid"] = self.payment.info_data["id"]
        ctx["method"] = self.payment.payment_provider.method
        return ctx


def success(request, *args, **kwargs):
    token = request.GET.get("token")
    payer = request.GET.get("PayerID")
    request.session["payment_paypal_token"] = token
    request.session["payment_paypal_payer"] = payer

    urlkwargs = {}
    if "cart_namespace" in kwargs:
        urlkwargs["cart_namespace"] = kwargs["cart_namespace"]

    if request.session.get("payment_paypal_payment"):
        payment = OrderPayment.objects.get(
            pk=request.session.get("payment_paypal_payment")
        )
    else:
        payment = None

    if request.session.get("payment_paypal_oid", None):
        if payment:
            prov = Paypal(request.event)
            try:
                resp = prov.execute_payment(request, payment)
            except PaymentException as e:
                messages.error(request, str(e))
                urlkwargs["step"] = "payment"
                return redirect(
                    eventreverse(
                        request.event, "presale:event.checkout", kwargs=urlkwargs
                    )
                )
            if resp:
                return resp
    else:
        messages.error(request, _("Invalid response from PayPal received."))
        logger.error("Session did not contain payment_paypal_oid")
        urlkwargs["step"] = "payment"
        return redirect(
            eventreverse(request.event, "presale:event.checkout", kwargs=urlkwargs)
        )

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
        # There can only be one payment method that does not have multi_use_supported, remove all
        # previous ones.
        cs = cart_session(request)
        cs["payments"] = [
            p for p in cs.get("payments", []) if p.get("multi_use_supported")
        ]
        add_payment_to_cart(request, PaypalWallet(request.event), None, None, None)
        urlkwargs["step"] = "confirm"
        return redirect(
            eventreverse(request.event, "presale:event.checkout", kwargs=urlkwargs)
        )


def abort(request, *args, **kwargs):
    messages.error(request, _("It looks like you canceled the Orange Money payment"))


def get_link(links, rel):
    for link in links:
        if link["rel"] == rel:
            return link

    return None
