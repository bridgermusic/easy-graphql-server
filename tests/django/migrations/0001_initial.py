# Generated by Django 4.0 on 2022-01-04 13:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=255, unique=True)),
                ('first_name', models.CharField(max_length=32)),
                ('last_name', models.CharField(max_length=64)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('is_staff', models.BooleanField(blank=True, default=False)),
                ('is_superuser', models.BooleanField(blank=True, default=False)),
            ],
            options={
                'db_table': 'auth_user',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='House',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('location', models.CharField(max_length=255)),
                ('construction_date', models.DateField(blank=True, null=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='houses', to='django.person')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='DailyOccupation',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('hours_per_day', models.IntegerField()),
                ('occupation', models.CharField(choices=[('EAT', 'EAT'), ('SLEEP', 'SLEEP'), ('WORK', 'WORK'), ('COMMUTE', 'COMMUTE'), ('_', '_')], max_length=7)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_occupations', to='django.person')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('iban', models.CharField(max_length=34)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_accounts', to='django.person')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.AddField(
            model_name='person',
            name='home',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tenants', to='django.house'),
        ),
    ]