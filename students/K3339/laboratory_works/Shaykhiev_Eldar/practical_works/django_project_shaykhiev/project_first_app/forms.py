from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Car, CarOwner


class OwnerForm(UserCreationForm):
    # Пользователь с атрибутами автовладельца: логин и пароль даёт UserCreationForm
    class Meta:
        model = CarOwner
        fields = ('username', 'last_name', 'first_name', 'birth_date',
                  'passport_number', 'home_address', 'nationality')
        widgets = {'birth_date': forms.DateInput(attrs={'type': 'date'})}


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['license_plate', 'brand', 'model', 'color']
