# Generated by Django 3.0.7 on 2020-09-28 11:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0012_auto_20200928_1236'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='primarytags',
            options={'verbose_name': 'Primary Tag', 'verbose_name_plural': 'Primary Tags'},
        ),
    ]
