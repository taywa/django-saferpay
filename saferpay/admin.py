from django.contrib import admin
from saferpay import models


class SaferpayResponseInline(admin.StackedInline):
    model = models.SaferpayResponse
    extra = 0
    readonly_fields = [
        'status_code',
        'time_created',
        'url',
        'payload',
        'response',
        'response_time',
        'transaction',
    ]


class SaferpayTransactionAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'token', 'status', 'date_created']
    readonly_fields = [
        'token',
        'order_id',
        'has_notify',
        'notify_token',
        'date_created',
        'amount',
        'currency',
        'language_code',
        'transaction_id',
        'status',
    ]
    inlines = [SaferpayResponseInline]


admin.site.register(models.SaferpayTransaction, SaferpayTransactionAdmin)
