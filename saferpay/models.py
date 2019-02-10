from django.db import models
from django.conf import settings


class SaferpayTransaction(models.Model):
    STATUS_CHOICES = (
        ('NEW', 'NEW'),
        ('AUTHORIZED', 'AUTHORIZED'),
        ('CAPTURED', 'CAPTURED'),
        ('CANCELD', 'CANCELD'),
    )
    token = models.CharField(max_length=32, primary_key=True)
    order_id = models.IntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, null=True, blank=True)
    transaction_id = models.CharField(max_length=64, null=True)
    language_code = models.CharField(max_length=2, default='en')
    has_notify = models.BooleanField(default=False)
    notify_token = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='NEW')

    class Meta:
        ordering = ('-date_created',)


class SaferpayResponse(models.Model):
    url = models.URLField()
    status_code = models.IntegerField(default=200)
    transaction = models.ForeignKey('SaferpayTransaction', on_delete=models.CASCADE)
    time_created = models.TimeField(auto_now_add=True)
    response_time = models.FloatField(help_text='Response time in milliseconds')
    payload = models.TextField()
    response = models.TextField()

    @property
    def action(self):
        from saferpay.gateway import API_PATHS_LOOKUP
        lookup = self.url.replace(settings.SAFERPAY_APIURL, '')
        try:
            return API_PATHS_LOOKUP[lookup]
        except KeyError:
            return self.url
