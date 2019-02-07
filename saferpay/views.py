import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View
from . models import SaferpayTransaction


class NotifyView(View):
    def get(self, request, *args, **kwargs):
        notify_token = kwargs['notify_token']
        transaction = get_object_or_404(SaferpayTransaction, notify_token=notify_token)
        transaction.has_notify = True
        transaction.save()
        return HttpResponse(
            json.dumps({'notify_token': notify_token}), content_type='application/json'
        )
