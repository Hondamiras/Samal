from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-lg peer focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Полное имя',
            'id': 'name'
        })
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
