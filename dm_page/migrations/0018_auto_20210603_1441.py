# Generated by Django 3.1.7 on 2021-06-03 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0017_auto_20210530_1149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donation',
            name='date_donated',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
