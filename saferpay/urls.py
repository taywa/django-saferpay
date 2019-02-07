from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^notify/(?P<notify_token>.+)/$', views.NotifyView.as_view(), name='saferpay-notify'),
]
