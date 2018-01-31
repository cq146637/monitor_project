"""untitled URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url, include
from monitor import views

app_name = "monitor"
urlpatterns = [
    url('admin/', admin.site.urls),
    url('api/', include('monitor.result_urls')),
    url('get_host_id/', views.get_host_id),
    url(r'^triggers/$', views.triggers, name='triggers'),
    # url(r'triggers/$', views.triggers, name='triggers'),
    url(r'hosts/$', views.hosts, name='hosts'),
    url(r'host_groups/$', views.host_groups, name='host_groups'),
    url(r'hosts/(\d+)/$', views.host_detail, name='host_detail'),
    url(r'trigger_list/$', views.trigger_list, name='trigger_list'),
    url(r'this_host_detail.html/$', views.this_host_detail, name='this_host_detail'),
]
