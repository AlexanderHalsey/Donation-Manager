# Generated by Django 3.1.7 on 2021-09-06 15:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0036_auto_20210906_1550'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='donation',
            name='pdf_receipt',
        ),
    ]
