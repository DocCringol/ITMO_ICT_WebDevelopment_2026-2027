from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import RATING_MAX, RATING_MIN, Registration, Review, User


class BootstrapMixin:
    # Классы Bootstrap для всех полей, чтобы не перечислять виджеты в каждой форме
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = css


class SignUpForm(BootstrapMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'email', 'organization', 'academic_degree')


class RegistrationForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['topic', 'talk_title', 'abstract']
        widgets = {'abstract': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, conference, **kwargs):
        super().__init__(*args, **kwargs)
        # Секцию можно выбрать только из тематик этой конференции
        self.fields['topic'].queryset = conference.topics.all()


class ReviewForm(BootstrapMixin, forms.ModelForm):
    # Границы задаются полю, а не виджету: иначе Django ставит min=0 от PositiveSmallIntegerField
    rating = forms.IntegerField(label='Рейтинг', min_value=RATING_MIN, max_value=RATING_MAX)

    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {'text': forms.Textarea(attrs={'rows': 3})}


class ResultForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['result']
