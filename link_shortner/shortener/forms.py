from django import forms

class URLForm(forms.Form):
    long_url = forms.URLField(label='Ссылка для сокращения:', )