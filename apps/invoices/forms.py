from django import forms
from .models import Invoice, InvoiceItem


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'type', 'issue_date', 'discount_amount', 'deduct_stock', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'lang': 'fa'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'deduct_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'description', 'quantity', 'unit_price', 'discount_percent', 'tax_percent']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice, InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True,
)


class PaymentForm(forms.Form):
    METHOD_CHOICES = [
        ('نقدی', 'نقدی'),
        ('چکی', 'چکی'),
        ('کارت به کارت', 'کارت به کارت'),
        ('transfer', 'انتقال بانکی'),
        ('POS', 'دستگاه POS'),
        ('online', 'پرداخت آنلاین'),
    ]
    amount = forms.DecimalField(
        label='مبلغ پرداختی',
        max_digits=15, decimal_places=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    method = forms.ChoiceField(
        label='روش پرداخت',
        choices=METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
    )
