# Generated by Django 2.0.1 on 2018-01-18 10:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0003_auto_20180118_1821'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='template',
            name='template_self',
        ),
    ]
