from django import forms
from .models import Form, Shift_form_hadod,Shift_streatr,Location_Utm
from .models import Location

from django import forms
from .models import Mahfth, Erea, Gata, Eng, Unit
import re
from django import forms
from .models import Type_block, Type_natural

class verificationForm(forms.Form):
   verification_code=forms.CharField(max_length=6,label='رمز التحقق',)
class Location_UtmForm(forms.ModelForm):
    class Meta:
        model = Location_Utm
        fields = ['utm_zone', 'easting', 'northing']
CURRENCY_CHOICES = [
 ('', '---اختر العملة---'),
        ('دولار', 'دولار'),
        ('يورو', 'يورو'),
        ('ريال', 'ريال'),
        
    ]
CURRENCY_CHOICES_L=[
	('', '---اختار الاتجاة---'),
	('شمال', 'شمال'),
	('جنوب', 'جنوب' ),
	('شرق', 'شرق'),
	('غرب', 'غرب'),] 
CURRENCY_CHOICES_M=[
      ('', '---اختار الحدود--'),
      ('شارع', 'شارع'),
      ('جار', 'جار '),
     
      ('م+جار', 'م+جار'),] 
CURRENCY_CHOICES_T=[
      ('', '---اختار نوع الشارع---'),
      ('ترابي', 'ترابي'),
      ('اسفلتي', 'اسفلتي  '),

    ] 
from django import forms
from .models import Shift_form_hadod, Form

class Shift_form_hadodForm(forms.ModelForm):
    sh = forms.ChoiceField(
        label='الاتجاه',
        choices=CURRENCY_CHOICES_L,
        required=True,
    )
    quantity = forms.CharField(label='الأبعاد حسب الإسقاط', required=True)
    shar_atjah = forms.ChoiceField(
        label='الحدود',
        choices=CURRENCY_CHOICES_M,
        required=True,
    )
    width_street = forms.IntegerField(
        label='عرض الشارع',
        required=False,
        min_value=0,
        widget=forms.NumberInput()
    )
    type_street = forms.ChoiceField(
        label='نوع الشارع',
        choices=CURRENCY_CHOICES_T,
        required=False,
    )
    number_strate = forms.CharField(label='رقم الشارع', required=False)

    class Meta:
        model = Shift_form_hadod
        fields = ['number_strate', 'type_street', 'width_street', 'shar_atjah', 'quantity', 'sh']

    def __init__(self, *args, **kwargs):
        self.form_instance = kwargs.pop('form_instance', None)
        self.report_instance = kwargs.pop('report_instance', None)
        super().__init__(*args, **kwargs)
        self.update_street_fields()

    def update_street_fields(self):
        self.show_street_fields = (
            self.data.get('shar_atjah') == 'شارع'
            if self.data else self.initial.get('shar_atjah') == 'شارع'
        )
        for field in ['width_street', 'type_street', 'number_strate']:
            self.fields[field].required = self.show_street_fields
            self.fields[field].widget.attrs['visible'] = self.show_street_fields

    def clean(self):
        cleaned_data = super().clean()
        shar = cleaned_data.get('shar_atjah')
        width = cleaned_data.get('width_street')
        number_strate = cleaned_data.get('number_strate')

        if shar and shar.strip() == 'شارع':
            # التحقق من الحقول الإلزامية
            required_fields = ['type_street', 'number_strate']  # width_street أصبح اختياري
            for field in required_fields:
                value = cleaned_data.get(field)
                if value in [None, '']:
                    self.add_error(field, "هذا الحقل مطلوب.")

            # التحقق من عرض الشارع (>5 ويجب أن يكون زوجيًا) فقط إذا تم إدخال قيمة
            if width not in [None, '']:
                if width > 5 and width % 2 != 0:
                    self.add_error(
                        'width_street',
                        "إذا كان عرض الشارع أكبر من 5 يجب أن يكون رقمًا زوجيًا."
                    )
            else:
                # إزالة الحقل من cleaned_data بحيث لا يتم حفظ None في قاعدة البيانات
                if 'width_street' in cleaned_data:
                    del cleaned_data['width_street']

        return cleaned_data
from django.forms import BaseFormSet
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import formset_factory, BaseFormSet
from .forms import Shift_form_hadodForm
from .models import Shift_form_hadod, Form, report_masahi

# الفورمسيت المخصص
class BaseShiftFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        numbers_seen = {}
        for i, form in enumerate(self.forms):
            if not form.cleaned_data:
                continue

            shar = form.cleaned_data.get('shar_atjah')
            number_strate = form.cleaned_data.get('number_strate')

            if shar and shar.strip() == 'شارع':
                if not number_strate or number_strate.strip() == '':
                    form.add_error('number_strate', "رقم الشارع مطلوب إذا الخيار 'شارع'.")
                    continue

                number_strate = number_strate.strip()
                if number_strate in numbers_seen:
                    form.add_error(
                        'number_strate',
                        f"رقم الشارع مكرر في الصف {numbers_seen[number_strate]+1}!"
                    )
                else:
                    numbers_seen[number_strate] = i

class Shift_streatrForm(forms.ModelForm):
    #xxr = forms.ModelChoiceField(queryset=Mahther_line.objects.all(), label='رقم  الفرصة', required=True)
    sh = forms.ChoiceField(label='اسم  الاتجاة',
    choices=CURRENCY_CHOICES_L,
    required=True,
    ) 
    quantity = forms.CharField(label='البعد حسب الاسقاط', required=True)
    shar_atjah = forms.ChoiceField(label='الجوار',
    choices=CURRENCY_CHOICES_M,
    required=True,
    ) 
    width_street= forms.CharField(label='عرض  الشارع', required=False)
    type_street =forms.ChoiceField(label='نوع  الشارع', 
        choices=CURRENCY_CHOICES_T,
    required=False,)
    number_strate = forms.CharField(label='رقم  الشارع', required=False)
  

    class Meta:
        model = Shift_streatr
        fields = [ 'number_strate','type_street','width_street' ,'shar_atjah','quantity','sh']
    def __init__(self, *args, **kwargs):
         
         super().__init__(*args, **kwargs)
         self.update_street_fields()
    def update_street_fields(self):
        self.show_street_fields = self.data.get('shar_atjah') == 'شارع' if self.data else self.initial.get('shar_atjah') == 'شارع'
        self.fields['width_street'].required = self.show_street_fields
        self.fields['type_street'].required = self.show_street_fields
        self.fields['number_strate'].required = self.show_street_fields
        

       
        self.fields['width_street'].widget.attrs['visible'] = self.show_street_fields
        self.fields['type_street'].widget.attrs['visible'] = self.show_street_fields
        self.fields['number_strate'].widget.attrs['visible'] = self.show_street_fields
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('shar_atjah') == 'شارع':
            for field in ['width_street', 'type_street', 'number_strate']:
                if not cleaned_data.get(field):
                    self.add_error(field, "Ce champ est requis.")
                    
        return cleaned_data
        if hasattr(self.instance, 'xxr_id'):
            self.fields['xxr'].queryset = Mahther_line.objects.filter(id=self.instance.xxr_id)

class MahfthForm(forms.ModelForm):
    class Meta:
        model = Mahfth
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم المحافظة'}),
        }


class EreaForm(forms.ModelForm):
    class Meta:
        model = Erea
        fields = ['name', 'mahfth']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم المنطقة'}),
            'mahfth': forms.Select(attrs={'class': 'form-control'})
            }


class GataForm(forms.ModelForm):
    class Meta:
        model = Gata
        fields = ['name', 'erea']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم القطاع'}),
            'erea': forms.Select(attrs={'class': 'form-control'})
        }
          


class EngForm(forms.ModelForm):
    class Meta:
        model = Eng
        fields = ['name', 'gata']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم Eng'}),
            'gata': forms.Select(attrs={'class': 'form-control'})
        }



class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'mahfth']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم الوحدة'}),
            'mahfth': forms.Select(attrs={'class': 'form-control'})
        }



class TypeBlockForm(forms.ModelForm):
    class Meta:
        model = Type_block
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم نوع البلوك',
            })
        }
        labels = {
            'name': 'اسم نوع البلوك',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()

        if not name:
            raise forms.ValidationError("الاسم لا يمكن أن يكون فارغًا.")
        if len(name) < 3:
            raise forms.ValidationError("الاسم يجب أن يكون على الأقل 3 أحرف.")
        if not re.match(r'^[\u0621-\u064A a-zA-Z\s]+$', name):
            raise forms.ValidationError("الاسم يجب أن يحتوي فقط على أحرف ومسافات، بدون أرقام أو رموز.")

        return name


class TypeNaturalForm(forms.ModelForm):
    class Meta:
        model = Type_natural
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم النوع الطبيعي',
            })
        }
        labels = {
            'name': 'اسم النوع الطبيعي',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()

        if not name:
            raise forms.ValidationError("الاسم لا يمكن أن يكون فارغًا.")
        if len(name) < 3:
            raise forms.ValidationError("الاسم يجب أن يكون على الأقل 3 أحرف.")
        if not re.match(r'^[\u0621-\u064A a-zA-Z\s]+$', name):
            raise forms.ValidationError("الاسم يجب أن يحتوي فقط على أحرف ومسافات، بدون أرقام أو رموز.")

        return name
# forms.py
from django import forms
from .models import Type_seol, Type_kah
import re

class TypeSeolForm(forms.ModelForm):
    class Meta:
        model = Type_seol
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم Seol'})}

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("الاسم لا يمكن أن يكون فارغًا.")
        if len(name) < 3:
            raise forms.ValidationError("الاسم يجب أن يكون على الأقل 3 أحرف.")
        if re.search(r'\d', name):
            raise forms.ValidationError("الاسم لا يمكن أن يحتوي على أرقام.")
        return name

class TypeKahForm(forms.ModelForm):
    class Meta:
        model = Type_kah
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم Kah'})}

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("الاسم لا يمكن أن يكون فارغًا.")
        if len(name) < 3:
            raise forms.ValidationError("الاسم يجب أن يكون على الأقل 3 أحرف.")
        if re.search(r'\d', name):
            raise forms.ValidationError("الاسم لا يمكن أن يحتوي على أرقام.")
        return name


from django import forms
from .models import typ

class TypForm(forms.ModelForm):
    class Meta:
        model = typ
        fields = ['number']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'أدخل الرقم'}),
        }

    def clean_number(self):
        number = self.cleaned_data.get('number')
        if number is None:
            raise forms.ValidationError("الرقم لا يمكن أن يكون فارغًا.")
        if number <= 0:
            raise forms.ValidationError("الرقم يجب أن يكون أكبر من صفر.")
        return number
from django import forms
from .models import Type_talb_astshr
import re

class TypeTalbAstshrForm(forms.ModelForm):
    class Meta:
        model = Type_talb_astshr
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم نوع الطلب'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("الاسم لا يمكن أن يكون فارغًا.")
        if len(name) < 3:
            raise forms.ValidationError("الاسم يجب أن يكون على الأقل 3 أحرف.")
        if re.search(r'\d', name):
            raise forms.ValidationError("الاسم لا يمكن أن يحتوي على أرقام.")
        return name
# forms.py
from django import forms
from .models import Type_map

class TypeMapForm(forms.ModelForm):
    class Meta:
        model = Type_map
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل الاسم'}),
        }

# forms.py
from django import forms
from .models import Eng_nazol

class EngNazolForm(forms.ModelForm):
    class Meta:
        model = Eng_nazol
        fields = ['name', 'mahfth']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_name'}),
            'mahfth': forms.Select(attrs={'class': 'form-control', 'id': 'id_mahfth'}),
        }
