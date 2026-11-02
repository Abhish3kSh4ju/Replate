
from django.db import models
from django.utils import timezone

# Create your models here.
class LoginTable(models.Model):
    username = models.CharField(max_length = 100, blank = True, null = True)
    password = models.CharField(max_length = 100, blank = True, null = True)
    usertype = models.CharField(max_length = 100, blank = True, null = True)

class UserTable(models.Model):
    username = models.CharField(max_length = 100, blank = True, null = True)
    password = models.CharField(max_length = 100, blank = True, null = True)
    gender = models.CharField(max_length = 100, blank = True, null =True)
    email = models.EmailField(max_length = 100, blank = True, null = True)
    address = models.CharField(max_length = 100,blank = True, null = True)
    phone = models.IntegerField(blank = True, null = True)
    LOGINID = models.ForeignKey(LoginTable, on_delete = models.CASCADE, blank = True, null = True)

class DonorTable(models.Model):
    donorname = models.CharField(max_length = 100, blank = True, null = True)
    email = models.EmailField(max_length = 100, blank = True, null = True)
    address = models.TextField(blank = True, null = True)
    phone = models.IntegerField(blank = True, null = True)
    image = models.ImageField(upload_to='donor_photos/', blank=True, null=True)
    date_of_joining = models.DateField(blank = True, null = True,auto_now_add=True)
    pickup_location = models.CharField(max_length = 200, blank = True, null = True)
    LOGINID = models.ForeignKey(LoginTable, on_delete = models.CASCADE, blank = True, null = True)

class FoodInfoTable(models.Model):
    foodname = models.CharField(max_length = 100, blank = True, null = True)
    quantity = models.IntegerField(blank = True, null = True)
    foodtype = models.CharField(max_length = 100, blank = True, null = True)
    description = models.TextField(blank=True, null=True)
    image = models.FileField(upload_to='uploads/', blank = True, null = True)
    time_food_made = models.DateTimeField(blank = True, null = True)
    expiry_time = models.DateTimeField(blank=True, null=True)
    DONORID = models.ForeignKey(DonorTable, on_delete = models.CASCADE, blank = True, null = True)

    @property
    def is_expired(self):
        if self.expiry_time is None:
            return False
        return timezone.now() > self.expiry_time

class RequestTable(models.Model):
    date = models.DateField(auto_now_add = True, blank = True, null  = True)
    status = models.CharField(max_length = 100, blank = True, null = True)
    pickuptime = models.TimeField(blank = True, null = True)
    FOODINFOID = models.ForeignKey(FoodInfoTable, on_delete = models.CASCADE, blank = True, null = True)
    USERID = models.ForeignKey(UserTable, on_delete = models.CASCADE, blank = True, null = True)
    Quantity=models.IntegerField(blank = True, null = True)

class NotificationTable(models.Model):
    notification = models.CharField(max_length = 500, blank = True, null = True)
    date = models.DateField(auto_now_add = True, blank = True, null  = True)
    time = models.TimeField(auto_now_add = True, blank = True, null = True)
    REQUESTID = models.ForeignKey(RequestTable, on_delete = models.CASCADE, blank = True, null = True)
    DONORID = models.ForeignKey(DonorTable, on_delete = models.CASCADE, blank = True, null = True)
    notification_type = models.CharField(max_length = 50, blank = True, null = True)

class ComplaintTable(models.Model):
    complaint = models.TextField(blank = True, null = True)
    reply = models.TextField(blank = True, null = True)
    date = models.DateField(auto_now_add = True, blank = True, null  = True)
    USERID = models.ForeignKey(UserTable, on_delete = models.CASCADE, blank = True, null = True)
    DONORID = models.ForeignKey(DonorTable, on_delete = models.CASCADE, blank = True, null = True)
    usertype = models.CharField(max_length= 100, blank=True, null=True)

class FeedbackTable(models.Model):
    feedback = models.TextField(blank = True, null = True)
    rating = models.FloatField(blank = True, null = True)
    date = models.DateField(auto_now_add = True, blank = True, null  = True)
    USERID = models.ForeignKey(UserTable, on_delete = models.CASCADE, blank = True, null = True)
    DONORID = models.ForeignKey(DonorTable, on_delete = models.CASCADE, blank = True, null = True)
    usertype = models.CharField(max_length=100, blank = True, null = True)
    reply = models.CharField(max_length = 200, blank = True, null = True)

    
