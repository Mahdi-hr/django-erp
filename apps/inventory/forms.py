from django import forms
from .models import PurchaseRecord, WasteRecord, ReturnRecord, ProductPurchase


class PurchaseRecordForm(forms.ModelForm):
    class Meta:
        model = PurchaseRecord
        fields = ['material', 'quantity', 'unit_price', 'supplier', 'invoice_number', 'purchase_date', 'notes']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


PurchaseRecordFormSet = forms.formset_factory(
    PurchaseRecordForm,
    extra=1,
    can_delete=True,
)


class ProductPurchaseForm(forms.ModelForm):
    class Meta:
        model = ProductPurchase
        fields = ['product', 'quantity', 'unit_price', 'supplier', 'invoice_number', 'purchase_date', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


ProductPurchaseFormSet = forms.formset_factory(
    ProductPurchaseForm,
    extra=1,
    can_delete=True,
)


class WasteRecordForm(forms.ModelForm):
    class Meta:
        model = WasteRecord
        fields = ['waste_date', 'material', 'quantity', 'reason', 'production_order']
        widgets = {
            'waste_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'material': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'production_order': forms.Select(attrs={'class': 'form-select'}),
        }


class ReturnRecordForm(forms.ModelForm):
    class Meta:
        model = ReturnRecord
        fields = ['return_date', 'material', 'quantity', 'reason', 'source']
        widgets = {
            'return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'material': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
        }
