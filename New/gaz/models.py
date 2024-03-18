import datetime
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.

from django.db import models


# class Post(models.Model):
#     title = models.CharField(max_length=100)
#     content = models.TextField()
#     date_posted = models.DateTimeField(default=timezone.now)
#     author = models.ForeignKey(User, on_delete=models.CASCADE)
#
#     def __str__(self):
#         return self.title


class ResultTable(models.Model):
    id = models.AutoField(primary_key=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, default=None)

    all_rows = models.IntegerField(null=True, default=0)
    matched_count = models.IntegerField(null=True, default=0)
    unmathed_count = models.IntegerField(null=True, default=0)
    other_count = models.IntegerField(null=True, default=0)



    class Meta:
        db_table = 'gaz_reports'


class Result(models.Model):
    STATUS = (
        ('совпадает', 'совпадает'),
        ('Расходится', 'Расходится'),
        ('запись отсутсвует в транзакциях', 'запись отсутсвует в транзакциях'),
        ('запись отсутсвует в ЗВ', 'запись отсутсвует в ЗВ'),
    )

    WHY = (
        ('', ''),
        ('Данные заправочной ведомости некорректны', 'Данные заправочной ведомости некорректны'),
        ('Данные транзакционной ведомости некорректны', 'Данные транзакционной ведомости некорректны'),
        ('Другое', 'Другое'),
    )

    ACTIONS = (
        ('', ''),
        ('А', 'А'),
        ('Б', 'Б'),
        ('Другое', 'Другое'),
    )

    geo = models.CharField(max_length=100)
    card_id = models.BigIntegerField()
    date = models.DateField()
    matched = models.CharField(null=True, choices=STATUS)
    variance = models.FloatField()
    created_at = models.ForeignKey('ResultTable', on_delete=models.CASCADE)

    short_text = models.CharField(null=True)
    ts_model = models.CharField(null=True)
    ts_id = models.CharField(null=True)
    fuel_mark = models.CharField(null=True)
    driver_name = models.CharField(null=True)
    full_name = models.CharField(null=True)

    variance_reason = models.CharField(null=True, choices=WHY)
    actions = models.CharField(null=True, choices=ACTIONS)
    postscriptum = models.CharField(null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'gaz_result'
        ordering = ['card_id']


