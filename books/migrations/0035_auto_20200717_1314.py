# Generated by Django 3.0.7 on 2020-07-17 12:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0034_auto_20200717_1300'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taggedbook',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='books.Book'),
        ),
    ]
