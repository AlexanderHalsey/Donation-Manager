# Generated by Django 3.1.7 on 2021-09-09 10:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0040_auto_20210908_0029'),
    ]

    operations = [
        migrations.RenameField(
            model_name='donationreceipt',
            old_name='canceled',
            new_name='cancel',
        ),
    ]