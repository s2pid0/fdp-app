# Generated by Django 5.0 on 2024-03-04 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gaz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='actions',
            field=models.CharField(choices=[('А', 'А'), ('Б', 'Б'), ('Другое', 'Другое')], null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='driver_name',
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='fuel_mark',
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='full_name',
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='postscriptum',
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='short_text',
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='ts_id',
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='ts_model',
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='variance_reason',
            field=models.CharField(choices=[('Данные заправочной ведомости некорректны', 'Данные заправочной ведомости некорректны'), ('Данные транзакционной ведомости некорректны', 'Данные транзакционной ведомости некорректны'), ('Другое', 'Другое')], null=True),
        ),
    ]
