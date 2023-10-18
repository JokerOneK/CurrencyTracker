# Generated by Django 4.2.5 on 2023-09-28 12:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assignments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('char_code', models.CharField(max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='UserCurrency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('threshold', models.DecimalField(decimal_places=4, max_digits=8)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assignments.currency')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CurrencyData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assignments.currency')),
            ],
        ),
    ]
