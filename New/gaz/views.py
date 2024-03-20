import os
import time
import datetime
import json
import simplejson
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.core.serializers import serialize
from django.views.decorators.csrf import csrf_exempt


from .forms import UploadFileForm
from .forms import EditResultForm
from django.http import HttpResponse, HttpResponseRedirect
import numpy as np
import pandas as pd
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
    # print(query_reports)

    if request.method == 'DELETE':
        ResultTable.objects.get(pk=request.DELETE['delete-id']).delete()

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            files1 = form.cleaned_data['file_field1']
            files2 = form.cleaned_data['file_field2']
            handle_uploaded_file([files1, files2])
            res, all_rows, matched_count, unmatched_count, other_count = xls_processing()
            report = ResultTable(created_by=request.user.username, all_rows=all_rows, matched_count=matched_count, unmathed_count=unmatched_count, other_count=other_count)
            report.save()

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
    stats = ResultTable.objects.latest('id')
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

    return render(request, "gaz/success.html", {"result_query": result_query, "myFilter": myFilter, "stats": stats})


def result_delete(request, pk):
    report = get_object_or_404(ResultTable, pk=pk)
    if request.method == 'POST':
        report.delete()
        return redirect('/home/')

    return render(request, 'gaz/home.html', {'report': report})




@login_required(login_url='auth/')
def get_results(request, pk):
    stats = ResultTable.objects.latest('id')
    id_created = pk
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
        # print("я вынул пк из запроса: ", request.POST['pk'])
        editable_record = Result.objects.get(pk=request.POST['pk'])
        # print(editable_record)
        editable_record.variance_reason = request.POST['variance_reason']
        editable_record.actions = request.POST['actions']
        editable_record.postscriptum = request.POST['postscriptum']
        editable_record.save()
        # print(editable_record.variance_reason, ' ', editable_record.actions, ' ', editable_record.postscriptum)


    return render(request, "gaz/current.html", {"result_query": result_query, "myFilter": myFilter, "created_at": id_created, "stats": stats})



def get_record(request, pk):
    record_query = Result.objects.get(pk=pk)
    return render(request, "gaz/result.html", {"record_query": record_query})


def xls_processing():
    all_time=time.time()
    pd.set_option('mode.chained_assignment', None)
    gazmotor_path = ''
    gazmotor_comp_path = ''
    start_time = time.time()
    for root, dirs, files in os.walk(settings.MEDIA_ROOT):
        for file in os.listdir(root):
            if file.lower().endswith('.xlsx') and file.startswith('ЗВ'):
                gazmotor_path = os.path.join(root, file)
            elif file.lower().endswith('.xlsx') and file.startswith('Транзакции'):
                gazmotor_comp_path = os.path.join(root, file)
    print("ЧТЕНИЕ --- %s seconds ---" % (time.time() - start_time))
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
               "1520_K29",
               "1520_K30",
               "1520_K31",
               "1520_K32",
               "1520_K33",
               "1520_K36",
               "1520_K37",
               "1520_K40",
               "1520_K43",
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
                           "Заволжское ЛПУ",
                           "Починковское ЛПУ",
                           "Моркинское ЛПУ",
                           "Филиал УАВР УМТС",
                           "Садовая техника филиалов",
                           "Садовая техника Семеновское ЛП",
                           "Садовая техника БО Ласточка",
                           "Садовая техника Администрация",
                           "Садовая техника БХР Арзамас",
                           "Садовая техника филиалов",
                           }
    # для зв
    kind_fuel = {
        "101592ГН",
        "101595ГН",
        "1015ДТГН"

    }
    # для транз
    fuel_trs = {"Аи-92": "Аи-92",
                "ДТ ОПТИ": "ДТ",
                "Аи-95": "Аи-95",
                "G-95": "Аи-95",
                "ДТ": "ДТ",
                "Аи-92 Премиум": "Аи-92",
                "АИ-92 ОПТИ": "Аи-92",
                "ДТ Премиум": "ДТ"
                }

    fuel_trs_test = {"101592ГН": "Аи-92",
                "1015ДТГН": "ДТ",
                "101595ГН": "Аи-95",
                }
    start_time = time.time()

    #ОБРАБОТКА ЗВ
    def set_id(x):
        if x is not np.nan and x < 8000000:
            x = 10000000 + x
        return x

    def set_nan_by_fuel(x, fuel):
        if x not in fuel:
            x = np.nan
        return x

    def set_nan_by_ak(x, ak):
        if x not in ak:
            x = np.nan
        return x

    def set_nan_by_flag(x):
        if x == 'Помечен для удаления':
            x = np.nan
        return x

    def format_fuel(x, fuel):
        if x is not np.nan:
            x = fuel[x]
        return x

    start_time = time.time()
    gaz_orig['Номер карты'] = gaz_orig['Номер карты'].apply(set_id)
    gaz_orig['Марка топлива'] = gaz_orig['Марка топлива'].apply(set_nan_by_fuel, args=(kind_fuel, ))
    gaz_orig['Местоположение'] = gaz_orig['Местоположение'].apply(set_nan_by_ak, args=(name_AK, ))
    gaz_orig['Марка топлива'] = gaz_orig['Марка топлива'].apply(format_fuel, args=(fuel_trs_test, ))
    gaz_orig['Удалена'] = gaz_orig['Удалена'].apply(set_nan_by_flag)

    zv_format = time.time() - start_time
    gaz_orig.dropna(axis='index', subset=['Марка топлива', 'Номер карты', 'Удалена'], inplace=True, ignore_index=True)
    gaz_orig.sort_values(by=['Номер карты', 'Дата заправки', 'Марка топлива'], ignore_index=True, inplace=True)
    gaz_orig.loc[len(gaz_orig.index)] = pd.Series()

    # СУММИРОВАНИЕ ЗВ
    i = 0
    start_time = time.time()
    gaz_new = gaz_orig
    gaz_new['Объём топлива'] = gaz_new.groupby(by=['Номер карты', 'Дата заправки', 'Марка топлива'])['Объём топлива'].transform(lambda x: x.sum())
    gaz_new.drop_duplicates(subset=['Номер карты', 'Дата заправки', 'Марка топлива', 'Объём топлива'], inplace=True)
    gaz_new.dropna(axis='index', subset='Объём топлива', inplace=True, ignore_index=True)

    zv_summ = time.time() - start_time
    #ОБРАБОТКА ТРАНЗАКЦИЙ
    start_time = time.time()
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

    gaz_trans['Товар'] = gaz_trans['Товар'].apply(set_nan_by_fuel, args=(fuel_trs, ))
    gaz_trans['Группа карт'] = gaz_trans['Группа карт'].apply(set_nan_by_ak, args=(name_AK_Gazpromneft,))
    gaz_trans['Дата транзакции'] = gaz_trans['Дата транзакции'].apply(lambda x: x.normalize())
    gaz_trans['Номер карты'] = gaz_trans['Номер карты'].apply(lambda x: x % 100000000)
    gaz_trans['Товар'] = gaz_trans['Товар'].apply(format_fuel, args=(fuel_trs, ))

    gaz_trans.dropna(axis='index', how='any', subset='Товар', inplace=True, ignore_index=True)
    gaz_trans.sort_values(by=['Номер карты', 'Дата транзакции', 'Товар'], ignore_index=True, inplace=True)
    tranz_format = time.time() - start_time
    # СУММИРОВАНИЕ ТРАНЗАКЦИИ
    start_time = time.time()

    gaz_trans_new = gaz_trans
    gaz_trans_new['Количество'] = gaz_trans_new.groupby(by=['Номер карты', 'Дата транзакции', 'Товар'])['Количество'].transform(lambda x: x.sum())
    gaz_trans_new.drop_duplicates(subset=['Номер карты', 'Дата транзакции', 'Товар', 'Количество'], inplace=True)
    gaz_trans_new.dropna(axis='index', how='any', subset='Количество', inplace=True, ignore_index=True)

    tranz_summ = time.time() - start_time

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

    # СРАВНЕНИЕ
    i = 0
    k = 0
    j = 0
    start_time = time.time()
    # gaz_new.loc[len(gaz_new.index)] = np.nan
    # gaz_trans_new.loc[len(gaz_trans_new.index)] = np.nan
    while j < (len(gaz_trans_new.axes[0])-1) and i < (len(gaz_new.axes[0])-1):

        if float(gaz_trans_new.iloc[j]['Номер карты']) % 100000000 == float(gaz_new.iloc[i]['Номер карты']) % 100000000:
            if gaz_trans_new.iloc[j]['Дата транзакции'].normalize() == gaz_new.iloc[i]['Дата заправки'].normalize():
                if gaz_trans_new.iloc[j]['Количество'] != gaz_new.iloc[i]['Объём топлива'] or gaz_trans_new.iloc[j]['Товар'] != gaz_new.iloc[i]['Марка топлива']:

                    gaz_result.at[k, 'matched'] = 'Расходится'
                    gaz_result.loc[k, 'variance'] = float(gaz_trans_new.iloc[j]['Количество']) - float(gaz_new.iloc[i]['Объём топлива'])
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
                gaz_result.at[k, 'matched'] = 'запись отсутсвует в ЗВ'

                gaz_result.loc[k, 'short_text'] = gaz_trans_new.loc[j, 'Товар']
                gaz_result.loc[k, 'ts_model'] = gaz_trans_new.loc[j, 'ТС']
                gaz_result.loc[k, 'ts_id'] = gaz_trans_new.loc[j, 'ТС']
                gaz_result.loc[k, 'fuel_mark'] = gaz_trans_new.loc[j, 'Товар']
                gaz_result.loc[k, 'driver_name'] = gaz_trans_new.loc[j, 'Водитель']
                gaz_result.loc[k, 'full_name'] = gaz_trans_new.loc[j, 'Водитель']

                j += 1
                k += 1
        elif float(gaz_new.iloc[i]['Номер карты']) % 100000000 < float(gaz_trans_new.iloc[j]['Номер карты']) % 100000000:
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

            gaz_result.loc[k, 'short_text'] = gaz_trans_new.loc[j, 'Товар']
            gaz_result.loc[k, 'ts_model'] = gaz_trans_new.loc[j, 'ТС']
            gaz_result.loc[k, 'ts_id'] = gaz_trans_new.loc[j, 'ТС']
            gaz_result.loc[k, 'fuel_mark'] = gaz_trans_new.loc[j, 'Товар']
            gaz_result.loc[k, 'driver_name'] = gaz_trans_new.loc[j, 'Водитель']
            gaz_result.loc[k, 'full_name'] = gaz_trans_new.loc[j, 'Водитель']

            j += 1
            k += 1

    os.remove(gazmotor_comp_path)
    os.remove(gazmotor_path)
    comp = time.time() - start_time
    all_rows = len(gaz_result.axes[0])
    matched_count = len(gaz_result[gaz_result['matched'] == 'совпадает'].axes[0])
    unmathed_count = len(gaz_result[gaz_result['matched'] == 'Расходится'].axes[0])
    other_count = len(gaz_result[(gaz_result['matched'] == 'запись отсутсвует в ЗВ') | (gaz_result['matched'] == 'запись отсутсвует в транзакциях')].axes[0])


    print('ОБРАБОТКА ЗВ %s seconds' % zv_format)
    print('СУММИРОВАНИЕ ЗВ %s seconds' % zv_summ)
    print('ОБРАБОТКА ТРАНЗАКЦИЙ %s seconds' % tranz_format)
    print('СУММИРОВАНИЕ ТРАНЗАКЦИЙ %s seconds' % tranz_summ)
    print('СРАВНЕНИЕ %s seconds' % comp)
    print('ИТОГО  %s seconds' % (zv_format + zv_summ + tranz_format + tranz_summ + comp))
    print('Размер gaz_new: ', len(gaz_new.axes[0]), ' Остановился на ', i)
    print('Размер gaz_trans_new: ', len(gaz_trans_new.axes[0]), ' Остановился на ', j)
    gaz_result.to_excel('upload\РЕЗУЛЬТАТ.xlsx')

    print('ALL-TIME %s sec' % (time.time() - all_time))
    return gaz_result, all_rows, matched_count, unmathed_count, other_count
