# Generated by Django 3.1.7 on 2021-09-16 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0072_auto_20210916_1611'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paramètre',
            name='manual',
            field=models.URLField(blank=True, null=True, verbose_name='Lien'),
        ),
    ]