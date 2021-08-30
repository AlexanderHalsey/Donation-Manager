# Generated by Django 3.1.7 on 2021-08-27 14:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0028_contact_is_facilitator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dm_page.profile'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dm_page.contact'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='donation_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dm_page.donationtype'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='organisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dm_page.organisation'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='payment_mode',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dm_page.paymentmode'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dm_page.profile'),
        ),
    ]