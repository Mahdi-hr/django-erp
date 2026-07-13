from django import forms
from .models import Product, ProductMaterial


class ProductForm(forms.ModelForm):
    current_stock = forms.IntegerField(
        label='موجودی اولیه', required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
    )

    class Meta:
        model = Product
        fields = [
            'name', 'code', 'barcode', 'category', 'image', 'description',
            'profit_percent', 'fixed_profit', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profit_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fixed_profit': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductMaterialForm(forms.ModelForm):
    class Meta:
        model = ProductMaterial
        fields = ['material', 'quantity', 'unit']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
        }


ProductMaterialFormSet = forms.inlineformset_factory(
    Product, ProductMaterial,
    form=ProductMaterialForm,
    extra=1,
    can_delete=True,
)
