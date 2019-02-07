# django-saferpay

*Saferpay integration for django*

This packages uses the saferpay json api and the saferpay payment page interface.
See the official [saferpay json api](http://saferpay.github.io/jsonapi/#ChapterPaymentPage) for more information.

## django

I use this django package in cunjunction with django-oscar. It can work with other django shop systems,
nothing is tied to django-oscar.

first update `settings.py`:

```python
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

INSTALLED_APPS = [
    ...
    'saferpay',
]

...
SAFERPAY_APIURL = 'https://test.saferpay.com/api'
SAFERPAY_USERNAME = 'API_XXX'
SAFERPAY_PASSWORD = 'XXX'
SAFERPAY_CUSTOMERID = 'xxxxxx'  # a number
SAFERPAY_TERMINALID = 'xxxxxx'  # a number
SAFERPAY_SUCCESS_CAPTURE_URL = reverse_lazy('checkout:payment-capture')
SAFERPAY_SUCCESS_URL = reverse_lazy('checkout:thank-you')
SAFERPAY_FAIL_URL = reverse_lazy('checkout:payment-failed')
SAFERPAY_ORDER_TEXT_NR = _('Payment for the company XXX, Order nr. %s.')
SAFERPAY_FORCE_LIABILITYSHIFT_ACTIVE = False  # default: False
SAFERPAY_DO_NOTIFY = True  # default: False
...
```

You need to provide three URLs from your app for providing callbacks from the saferpay gateway. 

- `SAFERPAY_SUCCESS_CAPTURE_URL` - saferpay callback for a successfull capture of the amount
  after PAYMENTPAGE_INIT and PAYMENTPAGE_ASSERT
- `SAFERPAY_SUCCESS_URL` - everything went fine, saferpay callback to shop success url
- `SAFERPAY_FAIL_URL` - something went wrong, saferpay callback to shop failure url

in your project `urls.py`:

```python
...
        url(r'', include('saferpay.urls')),
...
```

## django-oscar example

This is an example implementation not meant for for copy & paste. A oscar shop can be setup
totally different. It should help to see all parts which needed to be changed

add new payment method to oscar in `settings.py`:

```python
...
OSCAR_PAYMENT_METHODS = (
    ('saferpay', _('Creditcard (Visa, Mastercard, etc..)')),
)
...
```

### Update your checkout `myshop/checkout/app.py`

```python

from django.conf.urls import url
from oscar.apps.checkout import app
from myshop.checkout import views


class CheckoutApplication(app.CheckoutApplication):
    shipping_address_view = views.ShippingAddressView
    shipping_method_view = views.ShippingMethodView
    payment_details_view = views.PaymentDetailsView
    payment_method_view = views.PaymentMethodView
    preview_view = views.PreviewView  # normally just in PaymentDetailsView, custom to this use-case
    payment_capture_view = views.PaymentCapture  # new view not in oscar
    thankyou_view = views.ThankYouView
    payment_failed_view = views.PaymentFailed  # new view not in oscar

    def get_urls(self):
        urls = [
            url(r'^$', self.index_view.as_view(), name='index'),

            # Shipping/user address views
            url(r'shipping-address/$', self.shipping_address_view.as_view(), name='shipping-address'),
            url(r'user-address/edit/(?P<pk>\d+)/$', self.user_address_update_view.as_view(), name='user-address-update'),
            url(r'user-address/delete/(?P<pk>\d+)/$', self.user_address_delete_view.as_view(), name='user-address-delete'),

            # Shipping method views
            url(r'shipping-method/$', self.shipping_method_view.as_view(), name='shipping-method'),

            # Payment views
            url(r'payment-details/$', self.payment_details_view.as_view(), name='payment-details'),
            url(r'payment-method/$', self.payment_method_view.as_view(), name='payment-method'),
            url(r'payment-failed/$', self.payment_failed_view.as_view(), name='payment-failed'),

            # Preview and thankyou
            url(r'preview/$', self.preview_view.as_view(), name='preview'),
            url(r'payment-capture/$', self.payment_capture_view.as_view(), name='payment-capture'),
            url(r'thank-you/$', self.thankyou_view.as_view(), name='thank-you'),
        ]
        return self.post_process_urls(urls)

application = CheckoutApplication()
```


### Update your views

Add it to your custom extended oscar checkout app views.

in `myshop/checkout/views.py`:

```python
...
from saferpay.gateway import SaferpayService
from saferpay import execptions as sp_execptions
...

def billing_address_for_saferpay(billing_address):
    data = {}
    data['FirstName'] = billing_address.first_name
    data['LastName'] = billing_address.last_name
    data['Street'] = billing_address.line1
    if billing_address.line2:
        data['Street2'] = billing_address.line2
    data['Zip'] = billing_address.postcode
    data['City'] = billing_address.city
    return data

# in your PaymentDetailsView in handle_payment()
class PaymentDetailsView(OrderPlacementMixin, generic.TemplateView):
    ...

    def handle_payment(self, order_number, total, **kwargs):
        payment_method = self.checkout_session._get('payment', 'payment_method')
        # invoice
        if payment_method == 'invoice':
            pass
            # nothing to do for invoice, no money collected

        # saferpay
        elif payment_method == 'saferpay
            language_code = translation.get_language()[0:2]
            saferpay_service = SaferpayService(
                order_id=order_number, amount=total.incl_tax, currency=total.currency,
                language_code=language_code
            )
            billing_address = self.get_billing_address(
                shipping_address=self.get_shipping_address(self.request.basket)
            )
            billing_address_data = billing_address_for_saferpay(billing_address)
            payload = saferpay_service.payload_init(billing_address=billing_address_data)

            # redirects to payment page
            try:
                token = saferpay_service.paymentpage_init(payload)
                self.checkout_session._set('payment', 'saferpay_token', token)
                raise RedirectRequired(saferpay_service.paymentpage_redirect().url)
            except sp_execptions.GatewayError as e:
                self.restore_frozen_basket()
                return redirect(reverse_lazy('checkout:payment-failed'))

# new class
class PaymentCapture(views.PaymentDetailsView):
    success_url = reverse_lazy('checkout:thank-you')
    pre_conditions = []

    def load_frozen_basket(self, basket_id):
        # Lookup the frozen basket that this txn corresponds to
        try:
            basket = Basket.objects.get(id=basket_id, status=Basket.FROZEN)
        except Basket.DoesNotExist:
            return None

        if Selector:
            basket.strategy = Selector().strategy(self.request)

        Applicator().apply(basket, self.request.user, request=self.request)

        return basket

    def get(self, request, *args, **kwargs):
        token = self.checkout_session._get('payment', 'saferpay_token')
        saferpay_service = SaferpayService.init_from_transaction(token=token)
        try:
            status = saferpay_service.paymentpage_assert()
        except (
            sp_execptions.GatewayError, sp_execptions.TransactionDeclined,
            sp_execptions.UnableToTakePayment, sp_execptions.PaymentError
        ) as e:
            self.restore_frozen_basket()
            return redirect(reverse_lazy('checkout:payment-failed'))
        if status == 'CAPTURED':
            source_type, is_created = models.SourceType.objects.get_or_create(
                name='saferpay')
            source = source_type.sources.model(
                source_type=source_type,
                amount_allocated=saferpay_service.amount,
                currency=saferpay_service.currency
            )
            self.add_payment_source(source)
            self.add_payment_event('CAPTURED', saferpay_service.amount)

            post_payment.send_robust(sender=self, view=self)

            # If all is ok with payment, try and place order
            logger.info("Order #%s: payment successful, placing order", saferpay_service.order_id)

            try:
                basket_id = self.checkout_session.get_submitted_basket_id()
                basket = self.load_frozen_basket(basket_id)
                shipping_address = self.get_shipping_address(basket)
                billing_address = self.get_billing_address(shipping_address=shipping_address)
                shipping_method = self.get_shipping_method(
                    basket=basket, shipping_address=shipping_address
                )
                shipping_charge = shipping_method.calculate(basket)
                order_total = Price(
                    saferpay_service.currency, saferpay_service.amount, saferpay_service.amount
                )
                order_kwargs = self.checkout_session._get('payment', 'order_kwargs')
                order_number = saferpay_service.order_id
                return self.handle_order_placement(
                    order_number, self.request.user,
                    basket, shipping_address, shipping_method, shipping_charge,
                    billing_address, order_total, **order_kwargs
                )
            except UnableToPlaceOrder as e:
                # It's possible that something will go wrong while trying to
                # actually place an order.
                msg = six.text_type(e)
                logger.error("Order #%s: unable to place order - %s",
                             order_number, msg, exc_info=True)
                self.restore_frozen_basket()
                return self.render_preview(
                    self.request, error=msg
                )

# updated to add payment_method
class ThankYouView(CheckoutSessionMixin, views.ThankYouView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['payment_method'] = self.checkout_session._get('payment', 'payment_method')
        ctx.update(kwargs)
        return ctx

# new class, redirect to preview on payment failure
class PaymentFailed(OrderPlacementMixin, View):
    def get(self, request, *args, **kwargs):
        self.restore_frozen_basket()
        error_txt = _("The payment was not successful, please try again or use a different payment method.")
        messages.error(
            request,
            error_txt
        )
        return redirect(reverse_lazy('checkout:preview'))
```

