# Generated by Django 3.0.7 on 2020-09-29 16:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0020_auto_20200929_1653'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booktags',
            name='category',
        ),
    ]
