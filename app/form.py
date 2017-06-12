# coding:utf-8
from django import forms
from app.models import Idc

class IdcForm(forms.ModelForm):
    class Meta:
        model = Idc
        fields = ['idc_name', "networr_bandwidth", "operator", 'room_type', 'Contact_person', 'phone', 'address', 'remark']