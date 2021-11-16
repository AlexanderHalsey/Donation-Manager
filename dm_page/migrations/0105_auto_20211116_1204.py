# Generated by Django 3.1.7 on 2021-11-16 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0104_paramètre_bcc'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='locked',
            name='contacts',
        ),
        migrations.RemoveField(
            model_name='locked',
            name='donation_list',
        ),
        migrations.RemoveField(
            model_name='locked',
            name='donation_types',
        ),
        migrations.RemoveField(
            model_name='locked',
            name='organisations',
        ),
        migrations.AlterField(
            model_name='profile',
            name='primary_address',
            field=models.JSONField(default=None, null=True),
        ),
    ]