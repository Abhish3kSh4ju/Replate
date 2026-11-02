from django.contrib import admin

from RePlate_app.models import *

# Register your models here.
admin.site.register(LoginTable)
admin.site.register(UserTable)
admin.site.register(DonorTable)
admin.site.register(FoodInfoTable)
admin.site.register(RequestTable)
admin.site.register(NotificationTable)
admin.site.register(ComplaintTable)
admin.site.register(FeedbackTable)

