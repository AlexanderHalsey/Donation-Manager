# Generated by Django 3.1.7 on 2021-09-16 17:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0073_auto_20210916_1615'),
    ]

    operations = [
        migrations.RenameField(
            model_name='formedudon',
            old_name='default',
            new_name='default_value',
        ),
        migrations.RenameField(
            model_name='naturedudon',
            old_name='default',
            new_name='default_value',
        ),
    ]