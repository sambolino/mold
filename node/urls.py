from django.conf.urls import url
from node import views
from django.conf import settings

urlpatterns = [
    url(r'^$', views.index),
    url(r'^calculate_sum/(?P<species_id>[\w-]+)/(?P<wavelength>\w+)/(?P<temperature>[\w.]+)/$', views.calculate_sum),
    url(r'^plot/(?P<species_id>[\w-]+)/(?P<temperature>[\w.]+)/$', views.plot),
    url(r'^get_wavelengths/(?P<species_id>[\w-]+)/$', views.get_wavelengths),
    url(r'^get_XY/(?P<species_id>[\w-]+)/(?P<n>[\w.]+)/(?P<l>[\w.]+)/$', views.get_XY),
    #url(r'^get_XY/(?P<species_id>[\w-]+)/(?P<n>[0-9]{2})/(?P<l>[0-9]{2})/$', views.get_XY),
]
