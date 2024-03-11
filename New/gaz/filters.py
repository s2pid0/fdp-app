import django_filters
from django import forms
from django.forms import SelectMultiple

from .models import *

class ResultFilter(django_filters.FilterSet):
    matched = django_filters.ChoiceFilter(choices=Result.STATUS, label='Фильтр')

    class Meta:
        model = Result
        fields = ['matched']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.ChoiceFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                    'widget': forms.SelectMultiple(attrs={'class': 'filter-control'})
                },
            }
        }