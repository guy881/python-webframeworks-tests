from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.json_test_view, name='home'),
    url(r'^model$', views.model_test_view, name='model'),
    url(r'^load', views.load_test_view, name='load')
]
