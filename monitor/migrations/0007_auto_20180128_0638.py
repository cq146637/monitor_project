# Generated by Django 2.0.1 on 2018-01-27 22:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0006_auto_20180128_0637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventlog',
            name='trigger',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='monitor.Trigger'),
        ),
    ]