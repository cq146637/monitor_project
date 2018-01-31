from django.conf.urls import url
from qos import views

app_name = 'qos'

urlpatterns = [
    url(r'data/report/', views.data_report),
]

