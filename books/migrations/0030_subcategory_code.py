# Generated by Django 3.0.7 on 2024-10-03 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0029_auto_20241003_2044'),
    ]

    operations = [
        migrations.AddField(
            model_name='subcategory',
            name='code',
            field=models.CharField(default='TMP', max_length=3, unique=True),
            preserve_default=False,
        ),
    ]
