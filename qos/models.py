from django.db import models

# Create your models here.

from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete='CASCADE')
    name = models.CharField(max_length=32)
    sites = models.ManyToManyField('Site', blank=True, verbose_name=u"管理的站点")

    def __str__(self):
        return self.name


class Site(models.Model):
    name = models.CharField(max_length=64, verbose_name=u"站点名")
    url = models.CharField(max_length=255, unique=True)
    enabled = models.BooleanField(default=True, verbose_name=u"启用监测")

    def __str__(self):
        return self.url


class Region(models.Model):
    """
        每个地区为大的监控对象，地区监控指标具有概括性
    """
    name = models.CharField(max_length=64)
    region_id = models.IntegerField(u"区域ID", unique=True)
    region_type_choices = (('province', u'省'), ('city', u"城市"))
    region_type = models.CharField(choices=region_type_choices, max_length=32)
    child_of = models.ForeignKey('self', blank=True, null=True, verbose_name=u"父级", on_delete='CASCADE')

    def __str__(self):
        return self.name
