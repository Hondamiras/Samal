from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-lg peer focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Полное имя',
            'id': 'name'
        })
    )

    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-lg peer focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Телефон',
            'id': 'phone',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-lg peer focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Электронная почта',
            'id': 'email'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-lg peer focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Ваше сообщение',
            'id': 'message'
        })
    )

    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-callback': 'onRecaptchaSuccess'
            }
        )
    )