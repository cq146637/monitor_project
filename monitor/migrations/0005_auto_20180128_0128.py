# Generated by Django 2.0.1 on 2018-01-27 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0004_remove_template_template_self'),
    ]

    operations = [
        migrations.AlterField(
            model_name='triggerexpression',
            name='data_calc_func',
            field=models.CharField(choices=[('avg', 'Average'), ('max', 'Max'), ('hit', 'Hit'), ('last', 'Last')], default=1, max_length=64, verbose_name='数据处理方式'),
        ),
    ]