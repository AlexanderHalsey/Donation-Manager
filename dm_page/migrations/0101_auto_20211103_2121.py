# Generated by Django 3.1.7 on 2021-11-03 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0100_auto_20211103_1050'),
    ]

    operations = [
        migrations.AddField(
            model_name='paramètre',
            name='annual_process_button',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='locked',
            name='contacts',
            field=models.ManyToManyField(help_text='Attention! Laisser ce champ vide si vous voulez tout séléctioner.', to='dm_page.Contact', verbose_name='Contacts'),
        ),
        migrations.AlterField(
            model_name='locked',
            name='donation_types',
            field=models.ManyToManyField(help_text='Attention! Laisser ce champ vide si vous voulez tout séléctioner.', to='dm_page.DonationType', verbose_name='Types des Dons'),
        ),
        migrations.AlterField(
            model_name='locked',
            name='organisations',
            field=models.ManyToManyField(help_text='Attention! Laisser ce champ vide si vous voulez tout séléctioner.', to='dm_page.Organisation', verbose_name='Organisations'),
        ),
    ]
