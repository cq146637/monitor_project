# Generated by Django 2.0.1 on 2018-01-27 17:31

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('region_id', models.IntegerField(unique=True, verbose_name='区域ID')),
                ('region_type', models.CharField(choices=[('province', '省'), ('city', '城市')], max_length=32)),
                ('child_of', models.ForeignKey(blank=True, null=True, on_delete='CASCADE', to='qos.Region', verbose_name='父级')),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='站点名')),
                ('url', models.CharField(max_length=255, unique=True)),
                ('enabled', models.BooleanField(default=True, verbose_name='启用监测')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('sites', models.ManyToManyField(blank=True, to='qos.Site', verbose_name='管理的站点')),
                ('user', models.OneToOneField(on_delete='CASCADE', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]