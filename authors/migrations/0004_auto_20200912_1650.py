# Generated by Django 3.0.7 on 2020-09-12 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authors', '0003_auto_20200716_1332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='last_name',
            field=models.CharField(db_index=True, max_length=100),
        ),
    ]
