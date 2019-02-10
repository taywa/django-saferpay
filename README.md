# django-saferpay

*Saferpay integration for django*

This packages uses the saferpay json api and the saferpay payment page interface.
This is NOT an offical package from SIX Payment Services.

See the official [saferpay json api](http://saferpay.github.io/jsonapi/#ChapterPaymentPage) for more information.
Take also a look at [test.saferpay.com](https://test.saferpay.com/).

## django setup

This django package in used in cunjunction with django-oscar. It can work with other django shop systems,
nothing is tied to django-oscar.

It's used with dango 1.11 but should/could work with django 2.0, 2.1.

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
SAFERPAY_SUCCESS_CAPTURE_URL = reverse_lazy('yourshop:payment-capture')  # your callback after getting the money
SAFERPAY_SUCCESS_URL = reverse_lazy('yourshop:thank-you')  # your callback after a successfull order
SAFERPAY_FAIL_URL = reverse_lazy('yourshop:payment-failed')  # your callback after a failed payment
SAFERPAY_ORDER_TEXT_NR = _('Payment for the company XXX, Order nr. %s.')
SAFERPAY_FORCE_LIABILITYSHIFT_ACTIVE = False  # default: False
SAFERPAY_DO_NOTIFY = True  # default: False
...
```

You need to provide three URLs from your shop app for providing callbacks for the saferpay gateway. 

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

create the db models

```python
./manage.py migrate
```

### django oscar setup

If you use django oscar got to [django-oscar-saferpay](https://github.com/taywa/django-oscar-saferpay)
to procced with the setup process and see an sample usage implementation.

### sample usage

You can use this code as example. You need to integrate it into 
your own views in the shop system.

1. Intizialize the service

```python
from saferpay.gateway import SaferpayService
from saferpay import execptions as sp_execptions


def billing_address_for_saferpay(billing_address):
    """Transform you shop billing address to 
    a format that saferpay uses.
    Your billing_address object can be totaly differnt, 
    adjust it to your needs.
    """
    data = {}
    data['FirstName'] = billing_address.first_name
    data['LastName'] = billing_address.last_name
    data['Street'] = billing_address.line1
    if billing_address.line2:
        data['Street2'] = billing_address.line2
    data['Zip'] = billing_address.postcode
    data['City'] = billing_address.city
    return data


def payment_init(request, order):
    """
    Intizialize a new SaferpayService instance, with your
    order data. Adjust the the order calls for your shop.


    The init payload is created and after success you get
    redirected to the saferpay PayementPage.
    """
    saferpay_service = SaferpayService(
        order_id=order.number, amount=order.total.incl_tax,
        currency=order.total.currency, language_code=language_code
    )

    payload = saferpay_service.payload_init(billing_address=billing_address_data)

    try:
        token = saferpay_service.paymentpage_init(payload)
        request.session['saferpay_token'] = token
        raise RedirectRequired(saferpay_service.paymentpage_redirect().url)
    except sp_execptions.GatewayError as e:
        # do your rollback in case of payment failure 
        return redirect(reverse_lazy('yourshop:payment-failed'))
```

2. Assert and Capture the money and place the order

```python
from saferpay.gateway import SaferpayService
from saferpay import execptions as sp_execptions


def payment_capture(request):
    token = request.session['saferpay_token']
    saferpay_service = SaferpayService.init_from_transaction(token=token)
    try:
        status = saferpay_service.paymentpage_assert()
    except (
        sp_execptions.GatewayError, sp_execptions.TransactionDeclined,
        sp_execptions.UnableToTakePayment, sp_execptions.PaymentError
    ) as e:
        # do your rollback in case of payment failure 
        return redirect(reverse_lazy('yourshop:payment-failed'))
    if status == 'CAPTURED':
        # register the payment in you shop
        logger.info("Order #%s: payment successful, placing order", saferpay_service.order_id)

        try:
            # place the order
        except UnableToPlaceOrder as e:
            # go back to preview
```
