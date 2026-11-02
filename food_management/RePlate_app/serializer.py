from RePlate_app.models import *
from rest_framework.serializers import ModelSerializer

class UserSerializer(ModelSerializer):
    class Meta:
        model = UserTable
        fields = ['username','gender','phone','email','address','password']

class DonorSerializer(ModelSerializer):
    class Meta:
        model = DonorTable
        fields = ['donorname','email','address','phone','pickup_location','image']

class RequestSerializer(ModelSerializer):
    class Meta:
        model = RequestTable
        fields = ['status','pickuptime','FOODINFOID','Quantity','USERID']

class LoginSerializer(ModelSerializer):
    class Meta:
        model = LoginTable
        fields = ['username','password']

class ComplaintSerializer(ModelSerializer):
    class Meta:
        model = ComplaintTable
        fields = ['complaint','reply','usertype']

class FeedbackSerializer(ModelSerializer):
    class Meta:
        model = FeedbackTable
        fields = ['feedback','rating','usertype']

class FoodInfoSerializer(ModelSerializer):
    class Meta:
        model = FoodInfoTable
        fields = ['foodname','quantity','foodtype','description','image','time_food_made','expiry_time']

class NotificationSerializer(ModelSerializer):
    class Meta:
        model = NotificationTable
        fields = ['notification','notification_type', 'REQUESTID','DONORID']