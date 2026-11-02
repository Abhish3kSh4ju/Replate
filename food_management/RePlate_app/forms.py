from django.forms import ModelForm

from RePlate_app.models import *


class UserForm(ModelForm):
    class Meta:
        model=UserTable
        fields=['username','gender','phone','email','address','password']

class DonorForm(ModelForm):
    class Meta:
        model=DonorTable
        fields=['donorname','email','address','phone','pickup_location','image']

class RequestForm(ModelForm):
    class Meta:
        model = RequestTable
        fields = ['status','pickuptime','FOODINFOID','Quantity']


