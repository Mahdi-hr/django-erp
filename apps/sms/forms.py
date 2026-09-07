from django import forms
from .models import SMSTemplate, SMSProviderConfig


class SMSTemplateForm(forms.ModelForm):
    class Meta:
        model = SMSTemplate
        fields = ['name', 'title', 'body', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SendSMSForm(forms.Form):
    customers = forms.ModelMultipleChoiceField(
        label='مشتریان',
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )
    template = forms.ModelChoiceField(
        label='قالب',
        queryset=SMSTemplate.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    message = forms.CharField(
        label='متن پیامک',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'dir': 'rtl'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.customers.models import Customer
        self.fields['customers'].queryset = Customer.objects.filter(
            is_active=True
        ).order_by('name')


class SMSProviderConfigForm(forms.ModelForm):
    class Meta:
        model = SMSProviderConfig
        fields = ['provider', 'api_key', 'sender_number', 'is_active']
        widgets = {
            'provider': forms.Select(attrs={'class': 'form-select'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
