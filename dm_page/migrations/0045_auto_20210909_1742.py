# Generated by Django 3.1.7 on 2021-09-09 17:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0044_auto_20210909_1713'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ReceiptSettings',
            new_name='Paramètres',
        ),
        migrations.RenameModel(
            old_name='DonationReceipt',
            new_name='RecettesFiscales',
        ),
    ]