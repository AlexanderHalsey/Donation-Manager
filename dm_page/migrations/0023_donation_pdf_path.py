# Generated by Django 3.1.7 on 2021-07-04 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0022_donation_pdf'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='pdf_path',
            field=models.CharField(default='', max_length=200),
        ),
    ]