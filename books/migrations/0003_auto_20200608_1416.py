# Generated by Django 3.0.7 on 2020-06-08 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_auto_20200608_0229'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookinstance',
            name='publish_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
