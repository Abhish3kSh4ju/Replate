from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
import json
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views import *

from RePlate_app.models import *
from RePlate_app.forms import *

class Login(View):
    def get(self,request):
        return render(request,"Login.html")
    
    def post(self,request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            obj = LoginTable.objects.get(username = username,password = password)
            request.session['userid'] = obj.id
            if obj.usertype == 'admin':
                return HttpResponse(
                    "<script>alert('Login Successful');window.location='/Adminpanel';</script> "
                )
            elif obj.usertype == 'user':
                return HttpResponse(
                    "<script>alert('Login Successful');window.location='/Userpanel';</script> "
                )
            elif obj.usertype == 'donor':
                return HttpResponse(
                    "<script>alert('Login Successful');window.location='/Donorpanel';</script> "
                )
            else:
                return HttpResponse(
                    "<script>alert('Invalid User Type');window.location='/';</script>"
                )
        except LoginTable.DoesNotExist:
            return HttpResponse(
                 "<script>alert('Invalid Username or Password');window.location='/';</script>"
            )

class Logout(View):
    def get(self,request):
        request.session.flush()
        return redirect('/')
            
class Register(View):
    def get(self,request):
        return render(request,"Register.html")
    
    
class Usersignup(View):
    def get(self,request):
        return render(request,"Usersignup.html")
    
    def post(self,request):
        c=UserForm(request.POST)
        if c.is_valid():
            reg = c.save(commit=False)
            user = LoginTable.objects.create(username = reg.username,password = request.POST['password'],usertype = 'user')
            reg.LOGINID=user
            reg.save()
            return redirect('/Userpanel')
    
class Donorsignup(View):
    def get(self,request):
        return render(request,"Donorsignup.html")
    
    def post(self,request):
        c=DonorForm(request.POST,request.FILES)
        if c.is_valid():
         reg = c.save(commit=False)

         login_obj = LoginTable.objects.create(
             username = reg.donorname,
             password = request.POST['password'],
             usertype = 'donor',
         )

         donor = DonorTable.objects.create(
             donorname = reg.donorname,
             email = reg.email,
             address = reg.address,
             phone = reg.phone,
             image = reg.image,
             pickup_location = reg.pickup_location, 
             LOGINID = login_obj
         ) 
         donor.save()
         return redirect('/')
        return render(request,"Donorsignup.html",{'form':c})

#--------Admin---------
@method_decorator(never_cache, name='dispatch')
class Adminpanel(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        total_users = UserTable.objects.count()
        total_donors = DonorTable.objects.count()
        total_orders = RequestTable.objects.count()
        # Food saved = distinct food items that have at least one completed/confirmed order
        saved_food_ids = RequestTable.objects.exclude(
            status='Cancelled'
        ).values_list('FOODINFOID_id', flat=True).distinct()
        total_food_saved = FoodInfoTable.objects.filter(id__in=saved_food_ids).count()
        # Recent 5 orders
        recent_orders = RequestTable.objects.select_related(
            'USERID', 'FOODINFOID', 'FOODINFOID__DONORID'
        ).order_by('-id')[:5]
        # ── Build combined Recent Activity feed ──
        activities = []

        # 1. Food items registered by donors
        recent_food = FoodInfoTable.objects.select_related('DONORID').order_by('-id')[:5]
        for food in recent_food:
            donor_name = food.DONORID.donorname if food.DONORID else "A donor"
            activities.append({
                'icon': 'bi-cup-hot-fill',
                'color': 'green',
                'text': f'Donor "{donor_name}" has registered new food "{food.foodname or "a food item"}"',
                'sort_key': food.id,
                'sort_group': 1,
            })

        # 2. Orders placed / picked up
        recent_req = RequestTable.objects.select_related('USERID', 'FOODINFOID').order_by('-id')[:5]
        for req in recent_req:
            user_name = req.USERID.username if req.USERID else "A user"
            food_name = req.FOODINFOID.foodname if req.FOODINFOID else "food"
            if req.status == 'Completed':
                text = f'"{user_name}" picked up "{food_name}"'
                icon = 'bi-check-circle-fill'
                color = 'blue'
            elif req.status == 'Cancelled':
                text = f'"{user_name}" cancelled order for "{food_name}"'
                icon = 'bi-x-circle-fill'
                color = 'red'
            else:
                text = f'"{user_name}" ordered "{food_name}"'
                icon = 'bi-cart-check-fill'
                color = 'orange'
            activities.append({
                'icon': icon,
                'color': color,
                'text': text,
                'sort_key': req.id,
                'sort_group': 2,
            })

        # 3. New donors joined
        recent_donors = DonorTable.objects.order_by('-id')[:5]
        for donor in recent_donors:
            activities.append({
                'icon': 'bi-person-plus-fill',
                'color': 'blue',
                'text': f'New donor "{donor.donorname}" registered on Replate',
                'sort_key': donor.id,
                'sort_group': 3,
            })

        # No timestamps needed — just take a few recent items from each category
        recent_activities = (
            [a for a in activities if a['sort_group'] == 1][:2] +
            [a for a in activities if a['sort_group'] == 2][:2] +
            [a for a in activities if a['sort_group'] == 3][:2]
        )
        return render(request, "administration/Adminpanel.html", {
            'total_users': total_users,
            'total_donors': total_donors,
            'total_orders': total_orders,
            'total_food_saved': total_food_saved,
            'recent_orders': recent_orders,
            'recent_activities': recent_activities,
        })
#----------------------------------------------------------------------------------------------

@method_decorator(never_cache, name='dispatch')
class Adminuser(View):
    def get(self,request):
        if 'userid' not in request.session:
            return redirect('/')
        
        users = UserTable.objects.all()
        donors = DonorTable.objects.all()
    
        return render(request,"administration/Adminusers.html",{'users':users,'donors':donors})

#----------------------------------------------------------------------------------------------

@method_decorator(never_cache, name='dispatch')  
class Admincomplaints(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        user_complaint = ComplaintTable.objects.filter(USERID__isnull=False, usertype='admin').select_related('USERID')
        donor_complaint = ComplaintTable.objects.filter(DONORID__isnull=False, usertype='admin').select_related('DONORID')

        # Retrieve one-time messages set during POST
        success_msg = request.session.pop('complaint_reply_success', None)
        error_msg = request.session.pop('complaint_reply_error', None)

        return render(request, "administration/Admincomplaints.html", {
            'user_complaints': user_complaint,
            'donor_complaints': donor_complaint,
            'success_msg': success_msg,
            'error_msg': error_msg,
        })

    def post(self, request):
        if 'userid' not in request.session:
            return redirect('/')

        complaint_id = request.POST.get('complaint_id')
        reply_text = request.POST.get('reply', '').strip()
        delete_id = request.POST.get('delete_complaint_id')
        complaint_type = request.POST.get('complaint_type')

        # ── Handle delete ──────────────────────────────────────────────────────
        if delete_id:
            try:
                complaint_obj = ComplaintTable.objects.get(id=delete_id)
                complaint_obj.delete()
            except ComplaintTable.DoesNotExist:
                pass
            return redirect('Admincomplaints')

        # ── Handle reply ───────────────────────────────────────────────────────
        if not reply_text:
            request.session['complaint_reply_error'] = "Reply cannot be empty."
            return redirect('Admincomplaints')

        if complaint_id:
            try:
                complaint_obj = ComplaintTable.objects.get(id=complaint_id)
                complaint_obj.reply = reply_text
                complaint_obj.save()

                # NOTE: NotificationTable has no USERID field (removed in migration 0017).
                # User complaint replies are stored in ComplaintTable.reply and visible
                # to the user on their Usercomplaints page.
                # Donor notifications can still be sent via the DONORID FK.
                if complaint_type == 'donor' and complaint_obj.DONORID:
                    NotificationTable.objects.create(
                        notification=f"Admin replied to your complaint: {reply_text[:200]}",
                        DONORID=complaint_obj.DONORID,
                        notification_type='complaint'
                    )

                request.session['complaint_reply_success'] = "Reply sent successfully!"

            except ComplaintTable.DoesNotExist:
                request.session['complaint_reply_error'] = "Complaint not found."

        return redirect('Admincomplaints')
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name = 'dispatch')
class Adminfoodinfo(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        all_foods_qs = FoodInfoTable.objects.all()
        total_registered = all_foods_qs.count()

        # Evaluate queryset and sort: active first, expired last
        all_foods = sorted(list(all_foods_qs), key=lambda f: f.is_expired)

        expired_foods = [f for f in all_foods if f.is_expired]
        total_wasted = len(expired_foods)

        # "Saved" = distinct food items that have at least one order
        saved_food_ids = RequestTable.objects.values_list('FOODINFOID_id', flat=True).distinct()
        total_saved = FoodInfoTable.objects.filter(id__in=saved_food_ids).count()

        context = {
            'all_foods': all_foods,
            'total_registered': total_registered,
            'total_saved': total_saved,
            'total_wasted': total_wasted,
        }
        return render(request, "administration/Adminfoodinfo.html", context)
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Adminfeedback(View):
    def get(self,request):
     if 'userid' not in request.session:
         return redirect('/')

     feedback = FeedbackTable.objects.all()
     user_list=[]
     donor_list=[]
     for i in feedback:
        try:   
         user_list.append(i.USERID.id)
        except:
            donor_list.append(i.DONORID.id)
         
        user_feedback = FeedbackTable.objects.filter(USERID__in = user_list)
        donor_feedback = FeedbackTable.objects.filter(DONORID__in = donor_list)

     return render(request,'administration/Adminfeedback.html',{'user_feedbacks':user_feedback,'donor_feedback':donor_feedback})
    
    def post(self, request):
        feedback_id = request.POST.get('delete_feedback_id')
        feedback_type = request.POST.get('feedback_type')

        if feedback_id:
            FeedbackTable.objects.filter(id=feedback_id).delete()

        return redirect('Adminfeedback')
#-------------------------------------------Donor---------------------------------------------------  
@method_decorator(never_cache, name='dispatch')
class Donorpanel(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        now = timezone.now()
        all_donor_foods = FoodInfoTable.objects.filter(DONORID__LOGINID_id=request.session['userid'])

        # Only active (non-expired) foods for Recent Listings
        active_foods = [f for f in all_donor_foods if not f.is_expired]
        total_listings = all_donor_foods.count()
        active_count = len(active_foods)

        return render(request, "Donor/Donorpanel.html", {
            'foods': active_foods,
            'total_listings': total_listings,
            'active_count': active_count,
        })
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Donoraddfood(View):
    def get(self,request):
        if 'userid' not in request.session:
            return redirect('/')
        
        return render (request,"Donor/Donoraddfood.html")
    
    def post(self,request):
        foodname = request.POST.get('foodname')
        quantity = request.POST.get('quantity')
        foodtype = request.POST.get('foodtype')
        description = request.POST.get('description')
        time_food_made = request.POST.get("time_food_made")
        expiry_time = request.POST.get('expiry_time')
        image = request.FILES.get('image')

        donor_id = request.session.get('userid')
        donor = DonorTable.objects.get(LOGINID_id=donor_id)

        FoodInfoTable.objects.create(
            foodname=foodname,
            quantity=quantity,
            foodtype=foodtype,
            description=description,
            image=image,
            time_food_made=time_food_made,
            expiry_time=expiry_time,
            DONORID=donor
        )
        return redirect('/Donoraddfood')

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')    
class Donorcomplaint(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        donor = DonorTable.objects.get(LOGINID_id=request.session['userid'])
        # Complaints filed by THIS donor to admin
        my_complaints = ComplaintTable.objects.filter(DONORID=donor, usertype='admin')
        # Complaints filed by USERS against this donor
        user_complaints_against_donor = ComplaintTable.objects.filter(DONORID=donor, usertype='donor').select_related('USERID')
        return render(request, "Donor/Donorcomplaint.html", {
            'complaints': my_complaints,
            'user_complaints': user_complaints_against_donor
        })

    def post(self, request):
        complaint3 = request.POST['complaint']
        donor = DonorTable.objects.get(LOGINID_id=request.session['userid'])
        obj = ComplaintTable()
        obj.complaint = complaint3
        obj.usertype = 'admin'
        obj.reply = 'pending'
        obj.DONORID = donor
        obj.save()
        return redirect('Donorcomplaint')

#----------------------------------------------------------------------------------------------    
@method_decorator(never_cache, name='dispatch')
class Donorfeedback(View):
    def get(self,request):
        if 'userid' not in request.session:
            return redirect ('/')
        
        donor = DonorTable.objects.get(
            LOGINID__id = request.session['userid']
        )

        feedbacks = FeedbackTable.objects.filter(DONORID = donor)
        return render(request,"Donor/Donorfeedback.html",{'feedbacks':feedbacks})
    
    def post(self,request):
        feedback2 = request.POST['feedback']
        rating2 = request.POST['rating']
        obj = FeedbackTable()
        obj.feedback = feedback2
        obj.usertype = 'admin'
        obj.rating = rating2
        obj.DONORID = DonorTable.objects.get(LOGINID__id = request.session['userid'])
        obj.save()
        return redirect('Donorfeedback')

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')   
class Donorlisting(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        all_foods = list(FoodInfoTable.objects.filter(DONORID__LOGINID_id=request.session['userid']))
        # Active foods first, expired foods last
        sorted_foods = sorted(all_foods, key=lambda f: f.is_expired)
        return render(request, "Donor/Donorlisting.html", {'foods': sorted_foods})

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Donorprofile(View):

    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        user_id = request.session.get('userid')

        print("LOGIN ID :", user_id)

        donor = DonorTable.objects.filter(
            LOGINID_id=user_id
        ).first()

        print("DONOR :", donor)

        return render(
            request,
            "Donor/Donorprofile.html",
            {'donor': donor}
        )
#----------------------------------------------------------------------------------------------     
@method_decorator(never_cache, name='dispatch')
class Donoredit(View):
    def get(self,request):
        if 'userid' not in request.session:
            return redirect('/')
        
        user_id = request.session.get('userid')
        donor = DonorTable.objects.filter(LOGINID_id=user_id).first()
        return render(request,"Donor/Donoredit.html", {'donor': donor})
    

    def post(self, request):
        user_id = request.session.get('userid')
        donor = DonorTable.objects.filter(LOGINID_id=user_id).first()
        
        # We can use the form to validate and save, but since we are handling 
        # file uploads and specific fields, we can also do it manually or via DonorForm
        form = DonorForm(request.POST, request.FILES, instance=donor)
        if form.is_valid():
            form.save()
            return HttpResponse("<script>alert('Profile Updated Successfully');window.location='/Donorprofile';</script>")
        return render(request, "Donor/Donoredit.html", {'donor': donor, 'form': form})
    
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Donornotification(View):
    def get(self,request):
        if 'userid' not in request.session:
            return redirect('/')
        
        try:
            donor = DonorTable.objects.get(LOGINID_id=request.session['userid'])
            notifications = NotificationTable.objects.filter(DONORID=donor).order_by('-id')
        except DonorTable.DoesNotExist:
            notifications = []
        return render(request,"Donor/Donornotification.html", {'notifications': notifications})
    
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Sendcomplaintsdonor(View):
    def post(self,request):
        if 'userid' not in request.session:
            return redirect ('/')
        
        complaint1 = request.POST['complaint']
        donorid = request.POST['donor']
        obj = ComplaintTable()
        obj.complaint = complaint1
        obj.usertype = 'donor'
        obj.reply = 'pending'
        obj.DONORID = DonorTable.objects.get(id = donorid)
        obj.USERID = UserTable.objects.get(LOGINID_id = request.session['userid'])
        obj.save()
        
        # Send notification to donor
        NotificationTable.objects.create(
            notification=f"New complaint received from {obj.USERID.username}",
            DONORID=obj.DONORID,
            notification_type='complaint'
        )
        
        return redirect('Usercomplaints')
    
#----------------------------------------------------------------------------------------------    
@method_decorator(never_cache, name='dispatch')
class Sendcomplaintsadmin(View):
    def post(self,request):
        if 'userid' not in request.session:
            return redirect('/')
        
        complaint2 = request.POST['complaint']
        obj = ComplaintTable()
        obj.complaint = complaint2
        obj.usertype = 'admin'
        obj.reply = 'pending'
        obj.USERID = UserTable.objects.get(LOGINID_id = request.session['userid'])
        obj.save()
        return redirect('Usercomplaints')

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Sendfeedbackdonor(View):
    def post(self,request):
        if 'userid' not in request.session:
            return redirect('/')
        
        feedback1 = request.POST['feedback']
        rating1 = request.POST['rating']

        donor_id = request.POST['donorid']

        user = UserTable.objects.get(
            LOGINID = request.session['userid']
        )

        donor = DonorTable.objects.get(
            id = donor_id
        )

        obj = FeedbackTable()
        obj.feedback = feedback1
        obj.rating = rating1
        obj.USERID = user
        obj.DONORID = donor
        obj.usertype = 'user'

        obj.save()

        # Send notification to donor
        NotificationTable.objects.create(
            notification=f"New feedback received from {user.username} ({rating1}★)",
            DONORID=donor,
            notification_type='feedback'
        )

        return redirect('Userfeedback')
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Donorrequest(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        try:
            donor = DonorTable.objects.get(LOGINID_id=request.session['userid'])
            requests = RequestTable.objects.filter(FOODINFOID__DONORID=donor).order_by('-id')
        except DonorTable.DoesNotExist:
            requests = []
        return render(request, "Donor/Donorrequest.html", {'requests': requests})

    def post(self, request):
        if 'userid' not in request.session:
            return JsonResponse({'success': False, 'message': 'Please login first.'}, status=403)
            
        request_id = request.POST.get('request_id')
        new_status = request.POST.get('status')
        pickuptime = request.POST.get('pickuptime')
        
        if not request_id or not new_status:
            return JsonResponse({'success': False, 'message': 'Missing request ID or status.'})
            
        try:
            donor = DonorTable.objects.get(LOGINID_id=request.session['userid'])
            req_obj = RequestTable.objects.get(id=request_id, FOODINFOID__DONORID=donor)
            
            old_status = req_obj.status
            
            # Stock updates:
            is_new_active = new_status in ['Confirmed', 'Ready', 'Completed']
            is_old_active = old_status in ['Confirmed', 'Ready', 'Completed']
            
            if is_new_active and not is_old_active:
                food = req_obj.FOODINFOID
                if food.quantity is not None:
                    if food.quantity < req_obj.Quantity:
                        return JsonResponse({'success': False, 'message': f'Cannot confirm. Only {food.quantity} items available.'})
                    food.quantity -= req_obj.Quantity
                    food.save()
            elif not is_new_active and is_old_active:
                food = req_obj.FOODINFOID
                if food.quantity is not None:
                    food.quantity += req_obj.Quantity
                    food.save()
            
            req_obj.status = new_status
            if pickuptime:
                req_obj.pickuptime = pickuptime
            req_obj.save()
            
            # Send notification to the user
            msg = ""
            if new_status == 'Confirmed':
                msg = f"Your order #{req_obj.id} for {req_obj.FOODINFOID.foodname} has been confirmed."
            elif new_status == 'Ready':
                msg = f"Your order #{req_obj.id} for {req_obj.FOODINFOID.foodname} is ready for pickup."
            elif new_status == 'Cancelled':
                msg = f"Your order #{req_obj.id} for {req_obj.FOODINFOID.foodname} has been cancelled/rejected by the donor."
            elif new_status == 'Completed':
                msg = f"Your order #{req_obj.id} for {req_obj.FOODINFOID.foodname} has been marked as completed."
            
            if msg:
                # NOTE: NotificationTable has no USERID field (removed in migration 0017).
                # User notifications are fetched via REQUESTID__USERID in Usernotification view.
                NotificationTable.objects.create(
                    notification=msg,
                    REQUESTID=req_obj,
                    notification_type='order'
                )
            
            return JsonResponse({'success': True, 'message': f'Order status updated to {new_status} successfully.'})
            
        except DonorTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Donor profile not found.'})
        except RequestTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order request not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

#---------------------------------------User-------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Userpanel(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        donors = DonorTable.objects.all().order_by('id')[:3]  
        return render(request, "User/Userpanel.html", {
            'donors': donors,
        })
    
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Usercomplaints(View):
    def get(self,request):
        if 'userid' not in request.session:
            return redirect('/')

        donor = DonorTable.objects.all()

        complaints = ComplaintTable.objects.filter(
            USERID__LOGINID_id=request.session['userid']
        )

        return render(
            request,
            "User/Usercomplaints.html",
            {
                'donor': donor,
                'complaints': complaints
            }
        )
    
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Userfeedback(View):
    def get(self,request):
        if 'userid' not in request.session:
            return redirect('/')
        
        donor=DonorTable.objects.all()
        try:
            user = UserTable.objects.get(LOGINID_id=request.session['userid'])
            feedbacks = FeedbackTable.objects.filter(USERID=user).order_by('-id')
        except UserTable.DoesNotExist:
            feedbacks = []
        return render(request,"User/Userfeedback.html",{'donor':donor, 'feedbacks':feedbacks})

    def post(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        feedback = request.POST.get('feedback')
        rating = request.POST.get('rating')
        try:
            user = UserTable.objects.get(LOGINID_id=request.session['userid'])
            FeedbackTable.objects.create(
                feedback=feedback,
                rating=rating,
                USERID=user,
                usertype='admin'
            )
        except UserTable.DoesNotExist:
            pass
        return redirect('Userfeedback')

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Usernotification(View):
    def get (self,request):
        if 'userid' not in request.session:
            return redirect('/')
        try:
            user = UserTable.objects.get(LOGINID_id=request.session['userid'])
            notifications = NotificationTable.objects.filter(REQUESTID__USERID = user ).order_by('-id')
        except UserTable.DoesNotExist:
            notifications = []
        return render(request,"User/Usernotification.html", {'notifications': notifications})
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Userprofile(View):
    def get(self,request):
        if 'userid' not in request.session:
            return redirect('/')
        
        user_id = request.session.get('userid')
        user = UserTable.objects.get(LOGINID_id=user_id)
        return render(request,"User/userprofile.html",{'user':user})
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Edituser(View):
     def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        user_id = request.session.get('userid')
        user = UserTable.objects.get(LOGINID_id=user_id)
        return render(request, "User/Edituser.html", {'user': user})
     
     def post(self, request):
        user_id = request.session.get('userid')
        user = UserTable.objects.get(LOGINID_id=user_id)

        user.username = request.POST.get('username')
        user.phone = request.POST.get('phone')
        user.gender = request.POST.get('gender')
        user.email = request.POST.get('email')
        user.address = request.POST.get('address')
        user.save()
        return redirect ('Userprofile')
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Veg(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        now = timezone.now()
        veg_foods = FoodInfoTable.objects.filter(
            foodtype__iexact='veg'
        ).exclude(expiry_time__lt=now)
        return render(request, "User/Veg.html", {'veg_foods': veg_foods})
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Nonveg(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        now = timezone.now()
        non_vegfoods = FoodInfoTable.objects.filter(
            foodtype__iexact='Non-Veg'
        ).exclude(expiry_time__lt=now)
        return render(request, "User/Nonveg.html", {'non_vegfoods': non_vegfoods})

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Snacks(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        now = timezone.now()
        snacks = FoodInfoTable.objects.filter(
            foodtype__iexact='Snacks'
        ).exclude(expiry_time__lt=now)
        return render(request, "User/Snacks.html", {'snacks': snacks})
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Bakery(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        now = timezone.now()
        bakery = FoodInfoTable.objects.filter(
            foodtype__iexact='bakery'
        ).exclude(expiry_time__lt=now)
        return render(request, "User/Bakery.html", {'bakery': bakery})
    def post(self, request):
        form = RequestForm(request.POST)

        if form.is_valid():
            reg = form.save(commit=False)

            user = UserTable.objects.get(
                LOGINID_id=request.session['userid']
            )

            reg.USERID = user

            food_id = request.POST.get('FOODINFOID')
            reg.FOODINFOID_id = food_id

            reg.save()

            return redirect('/Bakery')

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Beverages(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        now = timezone.now()
        beverages = FoodInfoTable.objects.filter(
            foodtype__iexact='Beverage'
        ).exclude(expiry_time__lt=now)
        return render(request, "User/Beverages.html", {'beverages': beverages})
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Morerestaurants(View):
    def get (self, request):
        donors = DonorTable.objects.all()
        return render(request,"User/Morerestaurants.html",{'donors':donors})
    
from django.utils import timezone
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Restaurantfoods(View):
    def get(self, request, donorid):
        if 'userid' not in request.session:
          return redirect('/')
        
        donor = DonorTable.objects.get(id=donorid)
        foods = FoodInfoTable.objects.filter(
            DONORID=donor,
            expiry_time__gt=timezone.now()
        ).order_by('-id')
        return render(request, "User/Restaurantfoods.html", {
            'donor': donor,
            'foods': foods,
        })
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name = 'dispatch')
class PlaceOrder(View):
    def post(self, request):
        if 'userid' not in request.session:
          return redirect('/')
        
        if 'userid' not in request.session:
            return JsonResponse({'success': False, 'message': 'Please login first.'}, status=403)
        
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                food_id = data.get('food_id')
                quantity = data.get('quantity')
            except Exception:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data.'})
        else:
            food_id = request.POST.get('FOODINFOID')
            quantity = request.POST.get('Quantity')
            
        if not food_id or not quantity:
            return JsonResponse({'success': False, 'message': 'Missing food item or quantity.'})
            
        try:
            food = FoodInfoTable.objects.get(id=food_id)
            qty = int(quantity)
            
            if qty <= 0:
                return JsonResponse({'success': False, 'message': 'Quantity must be at least 1.'})
                
            if food.quantity is not None and food.quantity < qty:
                return JsonResponse({'success': False, 'message': f'Only {food.quantity} items available in stock.'})
                
            user = UserTable.objects.get(LOGINID_id=request.session['userid'])
            
            req = RequestTable.objects.create(
                status='Pending',
                FOODINFOID=food,
                USERID=user,
                Quantity=qty
            )
            
            # Send notification to donor
            NotificationTable.objects.create(
                notification=f"New food request placed by {user.username} for {food.foodname} (Qty: {qty})",
                REQUESTID=req,
                DONORID=food.DONORID,
                notification_type='order'
            )
            
            return JsonResponse({'success': True, 'message': f'"{food.foodname}" request placed successfully!'})
            
        except FoodInfoTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Food item not found.'})
        except UserTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User profile not found.'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid quantity.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
        
#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Dessert(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        desserts = FoodInfoTable.objects.filter(foodtype__iexact='Dessert')
        return render(request, "User/Dessert.html", {'desserts': desserts})

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Orders(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        try:
            user = UserTable.objects.get(LOGINID_id=request.session['userid'])
            requests = RequestTable.objects.filter(USERID=user).order_by('-id')
            
            orders_list = []
            for req in requests:
                food = req.FOODINFOID
                donor = food.DONORID if food else None
                orders_list.append({
                    'order_id': req.id,
                    'order_date': req.date.strftime("%B %d, %Y") if req.date else "N/A",
                    'status': req.status or 'Pending',
                    'food_name': food.foodname if food else "Deleted Item",
                    'food_image': food.image.url if food and food.image else "",
                    'quantity': req.Quantity,
                    'donor_name': donor.donorname if donor else "Unknown Donor",
                    'pickup_location': donor.pickup_location if donor else "N/A",
                    'pickup_datetime': req.pickuptime.strftime("%I:%M %p") if req.pickuptime else "N/A"
                })
        except UserTable.DoesNotExist:
            orders_list = []
        return render(request, "User/Orders.html", {'orders': orders_list})

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class CancelOrder(View):
    def post(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        if 'userid' not in request.session:
            return JsonResponse({'success': False, 'message': 'Please login first.'}, status=403)
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'success': False, 'message': 'Missing order ID.'})
        try:
            user = UserTable.objects.get(LOGINID_id=request.session['userid'])
            req_obj = RequestTable.objects.get(id=order_id, USERID=user)
            
            old_status = req_obj.status
            if old_status == 'Cancelled':
                return JsonResponse({'success': False, 'message': 'Order is already cancelled.'})
            if old_status == 'Completed':
                return JsonResponse({'success': False, 'message': 'Completed orders cannot be cancelled.'})
                
            # If the old status was Confirmed or Ready, we should restore stock
            if old_status in ['Confirmed', 'Ready']:
                food = req_obj.FOODINFOID
                if food.quantity is not None:
                    food.quantity += req_obj.Quantity
                    food.save()
                    
            req_obj.status = 'Cancelled'
            req_obj.save()
            
            # Send notification to donor
            NotificationTable.objects.create(
                notification=f"Order #{req_obj.id} for {req_obj.FOODINFOID.foodname} has been cancelled by {user.username}.",
                REQUESTID=req_obj,
                DONORID=req_obj.FOODINFOID.DONORID,
                notification_type='order'
            )
            
            return JsonResponse({'success': True, 'message': 'Order cancelled successfully.'})
        except UserTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User profile not found.'})
        except RequestTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class DonorReplyComplaint(View):
    def post(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        complaint_id = request.POST.get('complaint_id')
        reply_text = request.POST.get('reply')
        if not complaint_id or not reply_text:
            return redirect('Donorcomplaint')
        try:
            donor = DonorTable.objects.get(LOGINID_id=request.session['userid'])
            complaint_obj = ComplaintTable.objects.get(id=complaint_id, DONORID=donor)
            complaint_obj.reply = reply_text
            complaint_obj.save()
        except (DonorTable.DoesNotExist, ComplaintTable.DoesNotExist):
            return redirect('Donorcomplaint')

        # Send notification to user — separate block so a failure here never blocks the reply
        try:
            if complaint_obj.USERID:
                NotificationTable.objects.create(
                    notification=f"Donor {donor.donorname} replied to your complaint: {reply_text[:100]}",
                    USERID=complaint_obj.USERID,
                    notification_type='complaint'
                )
        except Exception:
            pass

        return redirect('Donorcomplaint')

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class DonorReplyFeedback(View):
    def post(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        feedback_id = request.POST.get('feedback_id')
        reply_text = request.POST.get('reply')
        if not feedback_id or not reply_text:
            return redirect('Donorfeedback')
        try:
            donor = DonorTable.objects.get(LOGINID_id=request.session['userid'])
            feedback_obj = FeedbackTable.objects.get(id=feedback_id, DONORID=donor)
            feedback_obj.reply = reply_text
            feedback_obj.save()
        except (DonorTable.DoesNotExist, FeedbackTable.DoesNotExist):
            return redirect('Donorfeedback')

        # Send notification to user — separate block so a failure never blocks the save
        try:
            if feedback_obj.USERID:
                NotificationTable.objects.create(
                    notification=f"Donor {donor.donorname} replied to your feedback: {reply_text[:100]}",
                    USERID=feedback_obj.USERID,
                    notification_type='feedback'
                )
        except Exception:
            pass
        return redirect('Donorfeedback')

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class Dessert(View):
    def get(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        now = timezone.now()
        desserts = FoodInfoTable.objects.filter(
            foodtype__iexact='Dessert'
        ).exclude(expiry_time__lt=now)
        return render(request, "User/Dessert.html", {'desserts': desserts})

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class DeleteFood(View):
    def post(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        if 'userid' not in request.session:
            return JsonResponse({'success': False, 'message': 'Not logged in.'}, status=403)
        food_id = request.POST.get('food_id')
        if not food_id:
            return JsonResponse({'success': False, 'message': 'Missing food ID.'})
        try:
            donor = DonorTable.objects.get(LOGINID_id=request.session['userid'])
            food = FoodInfoTable.objects.get(id=food_id, DONORID=donor)
            food.delete()
            return JsonResponse({'success': True, 'message': 'Food listing deleted.'})
        except DonorTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Donor profile not found.'})
        except FoodInfoTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Food not found or not yours.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class AdminDeleteUser(View):
    def post(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        user_id = request.POST.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Missing user ID.'})
        try:
            user_obj = UserTable.objects.get(id=user_id)
            # Also delete the associated LoginTable record
            if user_obj.LOGINID:
                user_obj.LOGINID.delete()   # cascades to UserTable
            else:
                user_obj.delete()
            return JsonResponse({'success': True, 'message': 'User deleted successfully.'})
        except UserTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

#----------------------------------------------------------------------------------------------
@method_decorator(never_cache, name='dispatch')
class AdminDeleteDonor(View):
    def post(self, request):
        if 'userid' not in request.session:
            return redirect('/')
        
        donor_id = request.POST.get('donor_id')
        if not donor_id:
            return JsonResponse({'success': False, 'message': 'Missing donor ID.'})
        try:
            donor_obj = DonorTable.objects.get(id=donor_id)
            if donor_obj.LOGINID:
                donor_obj.LOGINID.delete()  # cascades to DonorTable
            else:
                donor_obj.delete()
            return JsonResponse({'success': True, 'message': 'Donor deleted successfully.'})
        except DonorTable.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Donor not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

#------------------------------------API----------------------------------------------------------

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from RePlate_app.serializer import*

class LoginPage_api(APIView):
    def post(self,request):
        response_dict = {}
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            response_dict['message'] = "failed"
            return Response(response_dict,status=status.HTTP_400_BAD_REQUEST)
        t_user = LoginTable.objects.filter(username=username,password=password).first()
        if not t_user:
            response_dict['message'] = "invalid user"
            return Response(response_dict,status=status.HTTP_404_NOT_FOUND)
        else:
            response_dict['message'] = "success"
            response_dict['loginid'] = t_user.id
            response_dict['usertype'] = t_user.usertype
            return Response(response_dict,status=status.HTTP_200_OK)

class UserReg_api(APIView):
    def post(self,request):
        user_serial = UserSerializer(data=request.data)
        login_serial = LoginSerializer(data=request.data)
        data_valid = user_serial.is_valid()
        login_valid = login_serial.is_valid()
        if data_valid and login_valid:
            login_profile = login_serial.save(usertype = 'user')
            user_serial.save(LOGINID = login_profile)

            return Response(user_serial.data, status = status.HTTP_201_CREATED)
        return Response({
            'login error_errors': user_serial.error if not login_valid else None,

            'user_errors' : user_serial.error if not data_valid else None
        },status-status.HTTP_404_BAD_REQUEST)

class Donor_api(APIView):
    def get(self,request):
        d = DonorTable.objects.all()
        serializer = DonorSerializer(d,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class Userprofile_api(APIView):
    def get(self,request,id):
        p=UserTable.objects.get(LOGINID_id=id)
        serializer = UserSerializer(p)
        return Response(serializer.data,status=status.HTTP_200_OK)

class Orders_api(APIView):
    def get(self,request):
        o = RequestTable.objects.all()  
        serializer = RequestSerializer(o,many=True)
        print(serializer.data)
        return Response(serializer.data,status=status.HTTP_200_OK)

class UserComplaints_api(APIView):
    def post(self,request,id):
        print(request.data) 
        complaint1 = request.data.get('complaint')
        donorid = request.data.get('donor')
        print(donorid)
        obj = ComplaintSerializer(data = request.data)
        if obj.is_valid():
         complaint = obj.save(USERID = UserTable.objects.get(LOGINID_id = id),complaint=complaint1,reply = 'pending', DONORID = DonorTable.objects.get(id=donorid))
         complaint.save()
         return Response(obj.data, status = status.HTTP_200_OK)

class UserFeedback_api(APIView):
    def post(self, request,id):
        feedback1 = request.data.get('feedback')
        rating1 = request.data.get('rating')
        donorid = request.data.get('donor')
        obj = FeedbackSerializer( data = request.data)
        if obj.is_valid():
            feedback = obj.save(USERID = UserTable.objects.get(LOGINID_id = id), feedback = feedback1,rating = 'rating', DONORID = DonorTable.objects.get(id = donorid))
            feedback.save()
            return Response(obj.data, status = status.HTTP_200_OK)

#-----------------------------------------------Donor API ----------------------------------------

class Donoraddfood_api(APIView):
    def post (self,request,id):
        foodname = request.data.get('foodname')
        quantity = request.data.get('quantity')
        foodtype = request.data.get('foodtype')
        description = request.data.get('description')
        image = request.FILES.get('image')
        time_food_made = request.data.get('time_food_made')
        expiry_time = request.data.get('expiry_time')
        obj = FoodInfoSerializer(data = request.data)
        if obj.is_valid():
            foodinfo = obj.save(DONORID = DonorTable.objects.get(LOGINID_id = id), foodname = foodname, quantity = quantity, foodtype = foodtype, description = description,image = image, time_food_made=time_food_made, expiry_time = expiry_time)
            foodinfo.save()
            return Response(obj.data, status = status.HTTP_200_OK)

class DonorListing_api(APIView):
    def get(self,request,id):
        L = FoodInfoTable.objects.filter(DONORID_id = id)
        serializer = FoodInfoSerializer(L, many=True)
        return Response(serializer.data, status = status.HTTP_200_OK)

class DonorComplaint_api(APIView):
    def post(self,request,id):
        complaint2 = request.data.get('complaint')
        obj = ComplaintSerializer(data = request.data)
        if obj.is_valid():
            complaint = obj.save(DONORID = DonorTable.objects.get(LOGINID_id = id), complaint = complaint2, reply = 'pending', usertype = 'admin')
            complaint.save()
            return Response(obj.data, status = status.HTTP_200_OK)

class DonorFeedback_api(APIView):
    def post(self,request,id):
        feedback2 = request.data.get('feedback')
        rating2 = request.data.get('rating')
        obj = FeedbackSerializer(data = request.data)
        if obj.is_valid():
            feedback = obj.save(DONORID = DonorTable.objects.get(LOGINID_id = id), feedback = feedback2, rating = rating2, usertype = 'admin')
            feedback.save()
            return Response(obj.data, status = status.HTTP_200_OK)

class DonorNotification_api(APIView):
    def get(self,request,id):
        N = NotificationTable.objects.filter(DONORID_id = id)
        serializer = NotificationSerializer(N, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)