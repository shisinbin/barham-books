# Generated by Django 3.0.7 on 2020-09-11 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='title',
            field=models.CharField(db_index=True, max_length=250),
        ),
    ]
