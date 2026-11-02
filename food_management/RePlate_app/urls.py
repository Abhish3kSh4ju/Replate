"""
URL configuration for food_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from RePlate_app.views import *
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',Login.as_view(),name='Login'),
    path('Logout',Logout.as_view(), name = 'Logout'),
    path('Register',Register.as_view(),name = 'Register'),
    path('Usersignup',Usersignup.as_view(), name = 'Usersignup'),
    path('Donorsignup',Donorsignup.as_view(), name = 'Donorsignup'),


    path('Adminpanel',Adminpanel.as_view(),name ='Adminpanel'),
    path('Adminusers',Adminuser.as_view(),name ='Adminusers'),
    path('Admincomplaints',Admincomplaints.as_view(),name='Admincomplaints'),
    path('Adminfoodinfo',Adminfoodinfo.as_view(),name='Adminfoodinfo'),
    path('Adminfeedback',Adminfeedback.as_view(),name = 'Adminfeedback'),


    path('Userpanel',Userpanel.as_view(),name ='Userpanel'),
    path('Usercomplaints',Usercomplaints.as_view(),name='Usercomplaints'),
    path('Userfeedback',Userfeedback.as_view(),name = 'Userfeedback'),
    path('Userprofile',Userprofile.as_view(),name = 'Userprofile' ),
    path('Sendcomplaintsdonor',Sendcomplaintsdonor.as_view(),name = 'sendcomplaintsdonor'),
    path('Sendcomplaintsadmin',Sendcomplaintsadmin.as_view(), name = 'Sendcomplaintsadmin'),
    path('Sendfeedbackdonor',Sendfeedbackdonor.as_view(), name = 'Sendfeedbackdonor'),
    path('Usernotification',Usernotification.as_view(), name = 'Usernotification'),
    path('Morerestaurants',Morerestaurants.as_view(),name = 'Morerestaurants'),
    path('Restaurantfoods/<int:donorid>/', Restaurantfoods.as_view(), name='Restaurantfoods'),
    path('Veg',Veg.as_view(),name = 'Veg'),
    path('Nonveg',Nonveg.as_view(), name = 'Nonveg'),
    path('Snacks',Snacks.as_view(), name = 'Snacks'),
    path('Bakery',Bakery.as_view(), name = 'Bakery'),
    path('Beverages',Beverages.as_view(), name = 'Beverages'),
    path('Dessert',Dessert.as_view(), name = 'Dessert'),
    path('Orders',Orders.as_view(), name = 'Orders'),
    path('place_order/', PlaceOrder.as_view(), name='place_order'),
    path('cancel_order/', CancelOrder.as_view(), name='cancel_order'),
    path('donor_reply_complaint/', DonorReplyComplaint.as_view(), name='donor_reply_complaint'),
    path('donor_reply_feedback/', DonorReplyFeedback.as_view(), name='donor_reply_feedback'),
    path('Edituser',Edituser.as_view(), name = 'Edituser'),
    
    path('Donorpanel',Donorpanel.as_view(),name ='Donorpanel'),
    path('Donoraddfood',Donoraddfood.as_view(),name = 'Donoraddfood'),
    path('Donorcomplaint',Donorcomplaint.as_view(),name = 'Donorcomplaint'),
    path('Donorlisting',Donorlisting.as_view(),name = 'Donorlisting'),
    path('Donorfeedback',Donorfeedback.as_view(),name = 'Donorfeedback'),
    path('Donorprofile',Donorprofile.as_view(),name = 'Donorprofile'),
    path('Donoredit',Donoredit.as_view(),name = 'Donoredit'),
    path('Donornotification',Donornotification.as_view(),name = 'Donornotification'),
    path('Donorrequest',Donorrequest.as_view(),name = 'Donorrequest'),
    path('delete_food/', DeleteFood.as_view(), name='delete_food'),
    path('admin_delete_user/', AdminDeleteUser.as_view(), name='admin_delete_user'),
    path('admin_delete_donor/', AdminDeleteDonor.as_view(), name='admin_delete_donor'),

#---------------------------------------API-----------------------------------------------------------------

    path('LoginPage_api',LoginPage_api.as_view(),name = 'LoginPage_api'),
    path('UserReg_api', UserReg_api.as_view(),name = 'UserReg_api'),
    path('Donor_api',Donor_api.as_view(), name = 'Donor_api'),
    path('Userprofile_api/<int:id>', Userprofile_api.as_view(), name = 'Userprofile_api'),
    path('Orders_api', Orders_api.as_view(), name = 'Orders_api'),
    path('UserComplaints_api/<int:id>', UserComplaints_api.as_view(), name = 'UserComplaints_api'),
    path('UserFeedback_api/<int:id>', UserFeedback_api.as_view(), name = 'UserFeedback_api'),

#----------------------DONOR-----------------
    path('Donoraddfood_api/<int:id>',Donoraddfood_api.as_view(),name = 'Donoraddfood_api'),
    path('DonorListing_api/<int:id>',DonorListing_api.as_view(), name = 'DonorListing_api'),
    path('DonorComplaint_api/<int:id>',DonorComplaint_api.as_view(),name = 'DonorComplaint_api'),
    path('DonorFeedback_api/<int:id>',DonorFeedback_api.as_view(), name = 'DonorFeedback_api'),
    path('DonorNotification_api/<int:id>', DonorNotification_api.as_view(), name = 'DonorNotification_api'),
]
