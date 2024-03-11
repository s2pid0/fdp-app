import os
import datetime
import json
import simplejson
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.core import serializers
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.core.serializers import serialize
from django.views.decorators.csrf import csrf_exempt

from . import models
from .forms import UploadFileForm
from .forms import EditResultForm
from django.http import HttpResponse, HttpResponseRedirect
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from .models import Result
from .models import ResultTable
from .filters import ResultFilter
from django.conf import settings
from django.contrib.auth import logout



def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/auth/')

def handle_uploaded_file(files):
    for f in files:
        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT)
        with open(os.path.join(settings.MEDIA_ROOT, f.name), 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

@login_required()
def upload(request):
    query_reports = ResultTable.objects.all()
    print(query_reports)

    if request.method == 'DELETE':
        ResultTable.objects.get(pk=request.DELETE['delete-id']).delete()

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            files1 = form.cleaned_data['file_field1']
            files2 = form.cleaned_data['file_field2']
            handle_uploaded_file([files1, files2])
            res = xls_processing()
            report = ResultTable(created_by=request.user.username)
            report.save()
            print(report.id)
            res['created_at_id'] = report.id
            df_records = res.to_dict('records')
            model_instances = [Result(
                geo=record['geo'],
                card_id=record['card_id'],
                date=record['date'],
                matched=record['matched'],
                variance=record['variance'],
                created_at=report,

                short_text=record['short_text'],
                ts_model=record['ts_model'],
                ts_id=record['ts_id'],
                fuel_mark=record['fuel_mark'],
                driver_name=record['driver_name'],
                full_name=record['full_name'],

                variance_reason=record['variance_reason'],
                actions=record['actions'],
                postscriptum=record['postscriptum']
            ) for record in df_records]
            Result.objects.bulk_create(model_instances)
            return HttpResponseRedirect("/success/")
    else:
        form = UploadFileForm()
    return render(request, "gaz/home.html", {"form": form, "query_reports": query_reports})


@login_required(login_url='auth/')
@csrf_exempt
def check_terminal(request):
    def ajax(request):
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return True
        else:
            return False

    pk = ResultTable.objects.latest('id')
    result_query = Result.objects.filter(created_at=pk)
    myFilter = ResultFilter(request.GET, result_query)
    result_query = myFilter.qs

    print(ajax(request))

    if request.method == 'GET' and ajax(request):
        data = {
            'resps': serialize("json", result_query)
        }
        editResultForm = EditResultForm()
        if request.headers.get('show-form') == 'show-form':
            return HttpResponse(editResultForm.as_p())
        else:
            return JsonResponse(data, safe=False)

    if request.method == 'POST':
        editable_record = Result.objects.get(pk=request.POST['pk'])
        editable_record.variance_reason = request.POST['variance_reason']
        editable_record.actions = request.POST['actions']
        editable_record.postscriptum = request.POST['postscriptum']
        editable_record.save()


    return render(request, "gaz/success.html", {"result_query": result_query, "myFilter": myFilter})


def result_delete(request, pk):
    report = get_object_or_404(ResultTable, pk=pk)
    if request.method == 'POST':
        report.delete()
        return redirect('/home/')

    return render(request, 'gaz/home.html', {'report': report})




@login_required(login_url='auth/')
def get_results(request, pk):
    id_created = pk;
    result_query = Result.objects.all().filter(created_at=pk)
    def ajax(request):
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return True
        else:
            return False

    myFilter = ResultFilter(request.GET, result_query)
    result_query = myFilter.qs

    if request.method == 'GET' and ajax(request):
        data = {
            'resps': serialize("json", result_query)
        }
        editResultForm = EditResultForm()
        if request.headers.get('show-form') == 'show-form':
            return HttpResponse(editResultForm.as_p())
        else:
            return JsonResponse(data, safe=False)

    if request.method == 'POST':
        print("я вынул пк из запроса: ", request.POST['pk'])
        editable_record = Result.objects.get(pk=request.POST['pk'])
        print(editable_record)
        editable_record.variance_reason = request.POST['variance_reason']
        editable_record.actions = request.POST['actions']
        editable_record.postscriptum = request.POST['postscriptum']
        editable_record.save()
        print(editable_record.variance_reason, ' ', editable_record.actions, ' ', editable_record.postscriptum)


    return render(request, "gaz/current.html", {"result_query": result_query, "myFilter": myFilter, "created_at": id_created})



def get_record(request, pk):
    record_query = Result.objects.get(pk=pk)
    return render(request, "gaz/result.html", {"record_query": record_query})


def xls_processing():
    pd.set_option('mode.chained_assignment', None)
    gazmotor_path = ''
    gazmotor_comp_path = ''
    for root, dirs, files in os.walk(settings.MEDIA_ROOT):
        for file in os.listdir(root):
            if file.lower().endswith('.xlsx') and file.startswith('ЗВ'):
                gazmotor_path = os.path.join(root, file)
            elif file.lower().endswith('.xlsx') and file.startswith('Транзакции'):
                gazmotor_comp_path = os.path.join(root, file)

    gaz_orig = pd.read_excel(gazmotor_path)

    gaz_orig = pd.DataFrame(data=gaz_orig)
    gaz_new = pd.DataFrame(columns=gaz_orig.columns)

    collums_geo = {'1520_K10',
                   '1520_K11',
                   '1520_K12',
                   '1520_K15',
                   '1520_K18',
                   '1520_K19',
                   '1520_K20',
                   '1520_K24',
                   '1520_K25',
                   '1520_K27',
                   '1520_K31',
                   '1520_K32',
                   '1520_K33',
                   '1520_K37',
                   '1520_K40',
                   '1520_K44',
                   '1520_K45',
                   '1520_K48',
                   '1520_K52',
                   '1520_K53',
                   '1520_K54',
                   '1520_K55',
                   '1520_K56'
                   }

    fuel_trs = {'101592ГН',
                '1015ДТГН',
                '101595ГН',
                }

    # для зв
    name_AK = {"1520_K10",
               "1520_K11",
               "1520_K12",
               "1520_K15",
               "1520_K18",
               "1520_K19",
               "1520_K20",
               "1520_K24",
               "1520_K25",
               "1520_K27",
               "1520_K28",
               # "1520_K29",
               # "1520_K30",
               "1520_K31",
               "1520_K32",
               "1520_K33",
               # "1520_K36",
               "1520_K37",
               "1520_K40",
               # "1520_K43",
               "1520_K44",
               "1520_K45",
               "1520_K48",
               "1520_K52",
               "1520_K53",
               "1520_K54",
               "1520_K55",
               "1520_K56"
               }
    # для транз
    name_AK_Gazpromneft = {"УТТиСТ КОЛОННА 1",
                           "УТТиСТ КОЛОННА 2",
                           "Пензенское ЛПУ",
                           "Волжское ЛПУ",
                           "Арзамасское ЛПУ КС Лукоянов",
                           "Арзамасское ЛПУ КС Новоарзамас",
                           "Приокское ЛПУ",
                           "Владимирское ЛПУ",
                           "Вятское ЛПУ",
                           "Ивановское ЛПУ",
                           "Ласточка",
                           "Волга",
                           "УАВР",
                           "ИТЦ",
                           "Арзамасское ЛПУ",
                           "Чебоксарское ЛПУ",
                           "Кировское ЛПУ",
                           "Сеченовское ЛПУ",
                           "Торбеевское ЛПУ",
                           "Пильнинское ЛПУ",
                           "УМТС Доскино",
                           "Семеновское ЛПУ",
                           # "Заволжское ЛПУ",
                           # "Починковское ЛПУ",
                           # "Моркинское ЛПУ",
                           # "Филиал УАВР УМТС",
                           # "Садовая техника филиалов",
                           # "Садовая техника Семеновское ЛП",
                           # "Садовая техника БО Ласточка",
                           # "Садовая техника Администрация",
                           # "Садовая техника БХР Арзамас",
                           # "Садовая техника филиалов",
                           }
    # для зв
    kind_fuel = {
        "101592ГН",
        "101595ГН",
        "1015ДТГН"

    }
    # для транз
    fuel_trs = {"Аи-92",
                "ДТ ОПТИ",
                "Аи-95",
                "G-95",
                "ДТ",
                "Аи-92 Премиум",
                "АИ-92 ОПТИ",
                "ДТ Премиум"
                }

    # ОТСЕИВАНИЕ ЛИШНИХ ПО ТОПЛИВУ И ГЕО
    for row in range(gaz_orig.shape[0]):
        if gaz_orig.iloc[row]['Номер карты'] != np.nan and (gaz_orig.iloc[row]['Номер карты']) < 8000000:
            gaz_orig.loc[row, 'Номер карты'] = 10000000 + gaz_orig.iloc[row]['Номер карты']
        if gaz_orig.iloc[row]['Марка топлива'] not in kind_fuel or gaz_orig.iloc[row]['Местоположение'] not in name_AK:
            gaz_orig.loc[row] = np.nan
        if gaz_orig.iloc[row]['Удалена'] == 'Помечен для удаления':
            gaz_orig.loc[row] = np.nan

    gaz_orig.dropna(axis='index', subset='Марка топлива', inplace=True, ignore_index=True)
    gaz_orig.dropna(axis='index', subset='Номер карты', inplace=True, ignore_index=True)
    gaz_orig.sort_values(by=['Номер карты', 'Дата заправки'], ignore_index=True, inplace=True)
    gaz_orig.to_excel('обработанная ЗВ.xlsx')
    gaz_orig.loc[len(gaz_orig.index)] = pd.Series()
    # СУММИРОВАНИЕ ЗВ
    i = 0
    while i < len(gaz_orig.axes[0]) - 1:
        if gaz_orig.iloc[i]['Номер карты'] != np.nan:
            if gaz_orig.iloc[i]['Номер карты'] == gaz_orig.iloc[i + 1]['Номер карты'] and gaz_orig.iloc[i][
                'Дата заправки'] == gaz_orig.iloc[i + 1]['Дата заправки']:
                j = i
                sum = gaz_orig.iloc[i]['Объём топлива']
                while gaz_orig.iloc[i]['Номер карты'] == gaz_orig.iloc[j + 1]['Номер карты'] and gaz_orig.iloc[i][
                    'Дата заправки'] == gaz_orig.iloc[j + 1]['Дата заправки']:
                    sum += gaz_orig.iloc[j + 1]['Объём топлива']
                    gaz_orig.loc[j + 1] = np.nan
                    j += 1
                gaz_new.loc[i, 'Объём топлива'] = sum
                gaz_new.loc[i, gaz_new.columns != 'Объём топлива'] = gaz_orig.loc[
                    i, gaz_orig.columns != 'Объём топлива']
                i += 2
            else:
                gaz_new.loc[i, gaz_new.columns] = gaz_orig.loc[i, gaz_orig.columns]
                i += 1
        else:
            i += 1

    gaz_new.dropna(axis='index', subset='Объём топлива', inplace=True, ignore_index=True)

    gaz_trans = pd.read_excel(gazmotor_comp_path)
    k = 0
    n = 0

    for row in range(gaz_trans.shape[0]):
        if gaz_trans.iat[row, 0] == 'Номер карты':
            k = row
        if gaz_trans.iat[row, 0] == 'Итого:':
            n = row
            break

    gaz_trans = pd.read_excel(gazmotor_comp_path, 'Sheet1', skiprows=k + 1, nrows=n - k - 1)

    for row in range(gaz_trans.shape[0]):
        if gaz_trans.iloc[row]['Товар'] not in fuel_trs or gaz_trans.iloc[row][
            'Группа карт'] not in name_AK_Gazpromneft:
            gaz_trans.loc[row] = np.nan
    gaz_trans.sort_values(by=['Номер карты', 'Дата транзакции'], ignore_index=True, inplace=True)

    gaz_trans.dropna(axis='index', how='any', subset='Товар', inplace=True, ignore_index=True)

    gaz_trans_new = pd.DataFrame(columns=gaz_trans.columns)

    gaz_trans.loc[len(gaz_trans.index)] = pd.Series()
    # СУММИРОВАНИЕ ТРАНЗАКЦИИ
    row = 0
    while row < len(gaz_trans.axes[0]) - 1:
        if gaz_trans.iloc[row]['Номер карты'] == gaz_trans.iloc[row + 1]['Номер карты'] and gaz_trans.iloc[row][
            'Дата транзакции'].normalize() == gaz_trans.iloc[row + 1]['Дата транзакции'].normalize():
            j = row
            sum = gaz_trans.iloc[row]['Количество']
            while gaz_trans.iloc[row]['Номер карты'] == gaz_trans.iloc[j + 1]['Номер карты'] and gaz_trans.iloc[row][
                'Дата транзакции'].normalize() == gaz_trans.iloc[j + 1]['Дата транзакции'].normalize():
                sum += gaz_trans.iloc[j + 1]['Количество']
                gaz_trans.loc[j + 1] = np.nan
                j += 1

            curr_row = len(gaz_trans_new.index)
            gaz_trans_new.loc[curr_row, 'Количество'] = sum
            gaz_trans_new.loc[curr_row, gaz_trans_new.columns != 'Количество'] = gaz_trans.loc[
                row, gaz_trans.columns != 'Количество']
            row += 2
        else:
            gaz_trans_new.loc[len(gaz_trans_new.index)] = gaz_trans.iloc[row]
            row += 1

    gaz_trans_new.dropna(axis='index', how='any', subset='Количество', inplace=True, ignore_index=True)
    gaz_trans_new.sort_values(by=['Номер карты', 'Дата транзакции'], ignore_index=True, inplace=True)
    gaz_new.sort_values(by=['Номер карты', 'Дата заправки'], ignore_index=True, inplace=True)

    for j in range(gaz_trans_new.shape[0]):
        gaz_trans_new.loc[j, 'Номер карты'] = gaz_trans_new.loc[j, 'Номер карты'] % 100000000

    gaz_result = {'geo': [],
                  'card_id': [],
                  'date': [],
                  'matched': [],
                  'variance': [],
                  'created_at_id': [],

                  'short_text': [],
                  'ts_model': [],
                  'ts_id': [],
                  'fuel_mark': [],
                  'driver_name': [],
                  'full_name': [],

                  'variance_reason': [],
                  'actions': [],
                  'postscriptum': []
                  }

    gaz_result = pd.DataFrame.from_dict(gaz_result)
    print('таблицы обработаны!')
    # СРАВНЕНИЕ
    i = 0
    k = 0
    j = 0

    while j < len(gaz_trans_new.axes[0]) or i < len(gaz_new.axes[0]):
        if float(gaz_trans_new.iloc[j]['Номер карты']) % 100000000 == float(gaz_new.iloc[i]['Номер карты']) % 100000000:
            if gaz_trans_new.iloc[j]['Дата транзакции'].normalize() == gaz_new.iloc[i]['Дата заправки'].normalize():
                if gaz_trans_new.iloc[j]['Количество'] != gaz_new.iloc[i]['Объём топлива']:

                    gaz_result.at[k, 'matched'] = 'Расходится'
                    gaz_result.loc[k, 'variance'] = float(gaz_trans_new.iloc[j]['Количество']) - float(
                        gaz_new.iloc[i]['Объём топлива'])
                    gaz_result.loc[k, 'card_id'] = gaz_new.loc[i, 'Номер карты']
                    gaz_result.loc[k, 'date'] = gaz_new.loc[i, 'Дата заправки']
                    gaz_result.loc[k, 'geo'] = gaz_trans_new.loc[j, 'Группа карт']

                    gaz_result.loc[k, 'short_text'] = gaz_new.loc[i, 'Краткий текст материала']
                    gaz_result.loc[k, 'ts_model'] = gaz_new.loc[i, 'Модель ТС']
                    gaz_result.loc[k, 'ts_id'] = gaz_new.loc[i, 'Номерной знак ТС']
                    gaz_result.loc[k, 'fuel_mark'] = gaz_new.loc[i, 'Марка топлива']
                    gaz_result.loc[k, 'driver_name'] = gaz_new.loc[i, 'Имя пользователя']
                    gaz_result.loc[k, 'full_name'] = gaz_new.loc[i, 'Полное имя']

                    i += 1
                    j += 1
                    k += 1
                else:
                    gaz_result.loc[k, 'matched'] = 'совпадает'
                    gaz_result.loc[k, 'card_id'] = gaz_new.loc[i, 'Номер карты']
                    gaz_result.loc[k, 'date'] = gaz_new.loc[i, 'Дата заправки']
                    gaz_result.loc[k, 'geo'] = gaz_trans_new.loc[j, 'Группа карт']

                    gaz_result.loc[k, 'short_text'] = gaz_new.loc[i, 'Краткий текст материала']
                    gaz_result.loc[k, 'ts_model'] = gaz_new.loc[i, 'Модель ТС']
                    gaz_result.loc[k, 'ts_id'] = gaz_new.loc[i, 'Номерной знак ТС']
                    gaz_result.loc[k, 'fuel_mark'] = gaz_new.loc[i, 'Марка топлива']
                    gaz_result.loc[k, 'driver_name'] = gaz_new.loc[i, 'Имя пользователя']
                    gaz_result.loc[k, 'full_name'] = gaz_new.loc[i, 'Полное имя']

                    i += 1
                    j += 1
                    k += 1
            elif gaz_new.iloc[i]['Дата заправки'].normalize() < gaz_trans_new.iloc[j]['Дата транзакции'].normalize():
                gaz_result.loc[k, 'card_id'] = gaz_new.loc[i, 'Номер карты']
                gaz_result.loc[k, 'date'] = gaz_new.loc[i, 'Дата заправки']
                gaz_result.loc[k, 'geo'] = gaz_new.loc[i, 'Местоположение']
                gaz_result.at[k, 'matched'] = 'запись отсутсвует в транзакциях'

                gaz_result.loc[k, 'short_text'] = gaz_new.loc[i, 'Краткий текст материала']
                gaz_result.loc[k, 'ts_model'] = gaz_new.loc[i, 'Модель ТС']
                gaz_result.loc[k, 'ts_id'] = gaz_new.loc[i, 'Номерной знак ТС']
                gaz_result.loc[k, 'fuel_mark'] = gaz_new.loc[i, 'Марка топлива']
                gaz_result.loc[k, 'driver_name'] = gaz_new.loc[i, 'Имя пользователя']
                gaz_result.loc[k, 'full_name'] = gaz_new.loc[i, 'Полное имя']

                i += 1
                k += 1
            elif gaz_new.iloc[i]['Дата заправки'].normalize() > gaz_trans_new.iloc[j]['Дата транзакции'].normalize():
                gaz_result.loc[k, 'card_id'] = gaz_trans_new.loc[j, 'Номер карты']
                gaz_result.loc[k, 'date'] = gaz_trans_new.loc[j, 'Дата транзакции']
                gaz_result.loc[k, 'geo'] = gaz_trans_new.loc[j, 'Группа карт']
                gaz_result.at[k, 'matched'] = 'запись отсутсвует в ЗВ из-за даты'

                gaz_result.loc[k, 'short_text'] = gaz_trans_new.loc[i, 'Товар']
                gaz_result.loc[k, 'ts_model'] = gaz_trans_new.loc[i, 'ТС']
                gaz_result.loc[k, 'ts_id'] = gaz_trans_new.loc[i, 'ТС']
                gaz_result.loc[k, 'fuel_mark'] = gaz_trans_new.loc[i, 'Товар']
                gaz_result.loc[k, 'driver_name'] = gaz_trans_new.loc[i, 'Водитель']
                gaz_result.loc[k, 'full_name'] = gaz_trans_new.loc[i, 'Водитель']

                j += 1
                k += 1
        elif float(gaz_new.iloc[i]['Номер карты']) % 100000000 < float(
                gaz_trans_new.iloc[j]['Номер карты']) % 100000000:
            gaz_result.loc[k, 'card_id'] = gaz_new.loc[i, 'Номер карты']
            gaz_result.loc[k, 'date'] = gaz_new.loc[i, 'Дата заправки']
            gaz_result.loc[k, 'geo'] = gaz_new.loc[i, 'Местоположение']
            gaz_result.at[k, 'matched'] = 'запись отсутсвует в транзакциях'

            gaz_result.loc[k, 'short_text'] = gaz_new.loc[i, 'Краткий текст материала']
            gaz_result.loc[k, 'ts_model'] = gaz_new.loc[i, 'Модель ТС']
            gaz_result.loc[k, 'ts_id'] = gaz_new.loc[i, 'Номерной знак ТС']
            gaz_result.loc[k, 'fuel_mark'] = gaz_new.loc[i, 'Марка топлива']
            gaz_result.loc[k, 'driver_name'] = gaz_new.loc[i, 'Имя пользователя']
            gaz_result.loc[k, 'full_name'] = gaz_new.loc[i, 'Полное имя']

            i += 1
            k += 1
        else:
            gaz_result.loc[k, 'card_id'] = gaz_trans_new.loc[j, 'Номер карты']
            gaz_result.loc[k, 'date'] = gaz_trans_new.loc[j, 'Дата транзакции']
            gaz_result.loc[k, 'geo'] = gaz_trans_new.loc[j, 'Группа карт']
            gaz_result.at[k, 'matched'] = 'запись отсутсвует в ЗВ'

            gaz_result.loc[k, 'short_text'] = gaz_trans_new.loc[i, 'Товар']
            gaz_result.loc[k, 'ts_model'] = gaz_trans_new.loc[i, 'ТС']
            gaz_result.loc[k, 'ts_id'] = gaz_trans_new.loc[i, 'ТС']
            gaz_result.loc[k, 'fuel_mark'] = gaz_trans_new.loc[i, 'Товар']
            gaz_result.loc[k, 'driver_name'] = gaz_trans_new.loc[i, 'Водитель']
            gaz_result.loc[k, 'full_name'] = gaz_trans_new.loc[i, 'Водитель']

            j += 1
            k += 1


    gaz_result.to_excel('upload\РЕЗУЛЬТАТ.xlsx')


    return gaz_result
