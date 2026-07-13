from django import forms
from .models import Worker


class JalaliDateInput(forms.TextInput):
    input_type = 'text'

    def __init__(self, attrs=None):
        default_attrs = {'class': 'form-control jalali-date', 'autocomplete': 'off'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = [
            'name', 'phone', 'role', 'is_active',
            'national_id', 'address', 'birth_date', 'hire_date',
            'skill', 'experience_years', 'salary', 'insurance_number',
            'emergency_phone', 'description',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'birth_date': JalaliDateInput(attrs={'placeholder': 'تاریخ تولد'}),
            'hire_date': JalaliDateInput(attrs={'placeholder': 'تاریخ استخدام'}),
            'skill': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: جوشکاری CO2'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'insurance_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره بیمه'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'تلفن تماس اضطراری'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['birth_date', 'hire_date']:
            field = self.fields[name]
            if self.instance and self.instance.pk and getattr(self.instance, name, None):
                from apps.common.templatetags.jalali_filters import to_jalali
                import jdatetime
                val = getattr(self.instance, name)
                if hasattr(val, 'year'):
                    jalali_date = jdatetime.date.fromgregorian(date=val)
                    self.initial[name] = jalali_date.strftime('%Y/%m/%d')

    def clean_birth_date(self):
        return self._clean_jalali_date('birth_date')

    def clean_hire_date(self):
        return self._clean_jalali_date('hire_date')

    def _clean_jalali_date(self, field_name):
        val = self.cleaned_data.get(field_name)
        if not val:
            return None
        if hasattr(val, 'year'):
            return val
        try:
            parts = str(val).strip().split('/')
            if len(parts) == 3:
                import jdatetime
                jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
                jalali_date = jdatetime.date(jy, jm, jd)
                return jalali_date.togregorian()
        except Exception:
            pass
        return val
