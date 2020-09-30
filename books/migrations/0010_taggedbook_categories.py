# Generated by Django 3.0.7 on 2020-09-28 10:55

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0009_auto_20200927_1941'),
    ]

    operations = [
        migrations.AddField(
            model_name='taggedbook',
            name='categories',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=3), blank=True, null=True, size=None),
        ),
    ]
