# Generated by Django 3.0.7 on 2020-06-10 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0009_auto_20200609_0040'),
    ]

    operations = [
        migrations.AddField(
            model_name='genre',
            name='is_featured',
            field=models.BooleanField(default=False),
        ),
    ]
