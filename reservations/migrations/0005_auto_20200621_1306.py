# Generated by Django 3.0.7 on 2020-06-21 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0004_reservation_can_collect'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='can_collect',
            field=models.BooleanField(default=False),
        ),
    ]
