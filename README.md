# django-saferpay

*Saferpay integration for django*

This packages uses the saferpay json api and the saferpay payment page interface.
See the official [saferpay json api](http://saferpay.github.io/jsonapi/#ChapterPaymentPage) for more information.
Take also a look at [test.saferpay.com](https://test.saferpay.com/).

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
SAFERPAY_SUCCESS_CAPTURE_URL = reverse_lazy('checkout:payment-capture')  # your callback after getting the money
SAFERPAY_SUCCESS_URL = reverse_lazy('checkout:thank-you')  # your callback after a successfull order
SAFERPAY_FAIL_URL = reverse_lazy('checkout:payment-failed')  # your callback after a failed payment
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

create the db models

```python
./manage.py migrate
``

### django oscar

If you use django oscar got to (django-oscar-saferpay)[https://github.com/taywa/django-oscar-saferpay]
to procced with the setup process or the see an sample usage implementation.
