from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

# class UserRegisterForm(UserCreationForm):
#     email = forms.EmailField()
#
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'password1', 'password2']


class UserRegisterForm(forms.Form):
    username = forms.CharField(max_length=65, widget=forms.TextInput(attrs={"class": "login", "placeholder": "Логин"}), label='')
    password = forms.CharField(max_length=65, widget=forms.PasswordInput(attrs={"class": "password", "placeholder": "Пароль"}), label='')

