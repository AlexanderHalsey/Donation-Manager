# Generated by Django 3.1.7 on 2021-08-21 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0023_donation_pdf_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donation',
            name='pdf_path',
            field=models.CharField(default='', max_length=200, null=True),
        ),
    ]