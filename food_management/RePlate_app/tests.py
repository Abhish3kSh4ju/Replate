from django.test import TestCase, Client
from django.urls import reverse
from RePlate_app.models import LoginTable, UserTable, DonorTable, FoodInfoTable, RequestTable, FeedbackTable, ComplaintTable, NotificationTable
from datetime import datetime, timedelta

class RePlateE2ETestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create common login accounts
        self.admin_login = LoginTable.objects.create(username='admin', password='admin123', usertype='admin')
        
        self.user_login = LoginTable.objects.create(username='Abhi', password='abhi2004', usertype='user')
        self.user = UserTable.objects.create(username='Abhi', email='abhi@test.com', phone=1234567890, LOGINID=self.user_login)
        
        self.donor_login = LoginTable.objects.create(username='Top Form', password='topform123', usertype='donor')
        self.donor = DonorTable.objects.create(donorname='Top Form', email='topform@test.com', phone=9876543210, LOGINID=self.donor_login)
        
        # Create a food item listed by Donor
        self.food_item = FoodInfoTable.objects.create(
            foodname='Paneer Butter Masala',
            quantity=5,
            foodtype='Veg',
            description='Fresh and delicious paneer',
            time_food_made=datetime.now(),
            expiry_time=datetime.now() + timedelta(hours=6),
            DONORID=self.donor
        )

    def test_authentication_flow(self):
        # Test Login GET
        response = self.client.get(reverse('Login'))
        self.assertEqual(response.status_code, 200)
        
        # Test Login POST valid credentials (user redirect script)
        response = self.client.post(reverse('Login'), {'username': 'Abhi', 'password': 'abhi2004'})
        self.assertEqual(response.status_code, 200)
        self.assertIn("window.location='/Userpanel';", response.content.decode())
        
        # Test Login POST invalid credentials
        response = self.client.post(reverse('Login'), {'username': 'Abhi', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Invalid Username or Password", response.content.decode())

    def test_category_pages_load(self):
        # Set session first
        session = self.client.session
        session['userid'] = self.user_login.id
        session.save()
        
        categories = ['Veg', 'Nonveg', 'Snacks', 'Bakery', 'Beverages', 'Dessert']
        for cat in categories:
            response = self.client.get(reverse(cat))
            self.assertEqual(response.status_code, 200)

    def test_food_ordering_and_stock_validation(self):
        # Set session
        session = self.client.session
        session['userid'] = self.user_login.id
        session.save()
        
        # 1. Order food within stock limit
        response = self.client.post(reverse('place_order'), {
            'FOODINFOID': self.food_item.id,
            'Quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data['success'])
        
        # Verify request created in DB
        req = RequestTable.objects.filter(USERID=self.user, FOODINFOID=self.food_item).first()
        self.assertIsNotNone(req)
        self.assertEqual(req.status, 'Pending')
        self.assertEqual(req.Quantity, 2)
        
        # Stock should not change on Pending status (only when donor confirms)
        self.food_item.refresh_from_db()
        self.assertEqual(self.food_item.quantity, 5)

        # 2. Try ordering more than stock limit
        response = self.client.post(reverse('place_order'), {
            'FOODINFOID': self.food_item.id,
            'Quantity': 10
        })
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertFalse(res_data['success'])
        self.assertIn('available in stock', res_data['message'])

    def test_donor_request_status_update_and_stock_reduction(self):
        # Create a pending order request
        req = RequestTable.objects.create(
            status='Pending',
            FOODINFOID=self.food_item,
            USERID=self.user,
            Quantity=2
        )
        
        # Set Donor session
        session = self.client.session
        session['userid'] = self.donor_login.id
        session.save()
        
        # 1. GET requests dashboard page
        response = self.client.get(reverse('Donorrequest'))
        self.assertEqual(response.status_code, 200)
        
        # 2. POST to update request status to Confirmed (decrements stock)
        response = self.client.post(reverse('Donorrequest'), {
            'request_id': req.id,
            'status': 'Confirmed',
            'pickuptime': '18:30:00'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify stock decremented (5 - 2 = 3)
        self.food_item.refresh_from_db()
        self.assertEqual(self.food_item.quantity, 3)
        
        # Verify request status in DB
        req.refresh_from_db()
        self.assertEqual(req.status, 'Confirmed')
        
        # 3. POST to update request status to Cancelled (restores stock back to 5)
        response = self.client.post(reverse('Donorrequest'), {
            'request_id': req.id,
            'status': 'Cancelled'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify stock restored to 5
        self.food_item.refresh_from_db()
        self.assertEqual(self.food_item.quantity, 5)
        
        req.refresh_from_db()
        self.assertEqual(req.status, 'Cancelled')

    def test_feedback_flow(self):
        # Set User session
        session = self.client.session
        session['userid'] = self.user_login.id
        session.save()
        
        # 1. Submit Admin feedback
        response = self.client.post(reverse('Userfeedback'), {
            'feedback': 'Excellent admin responsiveness',
            'rating': 4
        })
        self.assertEqual(response.status_code, 302) # Redirect to Userfeedback GET
        
        # Verify feedback in DB
        fb_admin = FeedbackTable.objects.filter(USERID=self.user, usertype='admin').first()
        self.assertIsNotNone(fb_admin)
        self.assertEqual(fb_admin.feedback, 'Excellent admin responsiveness')
        self.assertEqual(fb_admin.rating, 4.0)

        # 2. Submit Donor feedback
        response = self.client.post(reverse('Sendfeedbackdonor'), {
            'feedback': 'Excellent donor promptness',
            'rating': 5,
            'donorid': self.donor.id
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify feedback in DB
        fb_donor = FeedbackTable.objects.filter(USERID=self.user, DONORID=self.donor).first()
        self.assertIsNotNone(fb_donor)
        self.assertEqual(fb_donor.feedback, 'Excellent donor promptness')
        self.assertEqual(fb_donor.rating, 5.0)
        
        # 3. GET Userfeedback history list page
        response = self.client.get(reverse('Userfeedback'))
        self.assertEqual(response.status_code, 200)
        # Check that both feedbacks appear in response content
        content = response.content.decode()
        self.assertIn('Excellent admin responsiveness', content)
        self.assertIn('Excellent donor promptness', content)

    def test_complaints_flow(self):
        # Set User session
        session = self.client.session
        session['userid'] = self.user_login.id
        session.save()
        
        # 1. Submit complaint to Admin
        response = self.client.post(reverse('Sendcomplaintsadmin'), {
            'complaint': 'Admin issue description'
        })
        self.assertEqual(response.status_code, 302)
        
        comp_admin = ComplaintTable.objects.filter(USERID=self.user, usertype='admin').first()
        self.assertIsNotNone(comp_admin)
        self.assertEqual(comp_admin.complaint, 'Admin issue description')
        
        # 2. Submit complaint to Donor
        response = self.client.post(reverse('sendcomplaintsdonor'), {
            'complaint': 'Donor issue description',
            'donor': self.donor.id
        })
        self.assertEqual(response.status_code, 302)
        
        comp_donor = ComplaintTable.objects.filter(USERID=self.user, DONORID=self.donor, usertype='donor').first()
        self.assertIsNotNone(comp_donor)
        self.assertEqual(comp_donor.complaint, 'Donor issue description')
        
        # 3. GET Usercomplaints history page
        response = self.client.get(reverse('Usercomplaints'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Admin issue description', content)
        self.assertIn('Donor issue description', content)

    def test_notification_connection_logic(self):
        # Set user session
        session = self.client.session
        session['userid'] = self.user_login.id
        session.save()

        # 1. User places order
        response = self.client.post(reverse('place_order'), {
            'FOODINFOID': self.food_item.id,
            'Quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify donor received notification
        notif = NotificationTable.objects.filter(DONORID=self.donor, notification_type='order').first()
        self.assertIsNotNone(notif)
        self.assertIn('New food request placed by Abhi', notif.notification)
        req = notif.REQUESTID
        self.assertEqual(req.Quantity, 2)

        # 2. User cancels order
        response = self.client.post(reverse('cancel_order'), {
            'order_id': req.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        # Verify donor received cancellation notification
        notif_cancel = NotificationTable.objects.filter(DONORID=self.donor, notification_type='order').order_by('-id').first()
        self.assertIsNotNone(notif_cancel)
        self.assertIn('has been cancelled by Abhi', notif_cancel.notification)
        
        # 3. Re-place order and Donor manages it (Confirm, Ready, Cancel)
        req2 = RequestTable.objects.create(
            status='Pending',
            FOODINFOID=self.food_item,
            USERID=self.user,
            Quantity=1
        )
        # Set Donor session
        session = self.client.session
        session['userid'] = self.donor_login.id
        session.save()
        
        # Confirm order
        response = self.client.post(reverse('Donorrequest'), {
            'request_id': req2.id,
            'status': 'Confirmed',
            'pickuptime': '12:00:00'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        # Verify user received confirm notification
        notif_user = NotificationTable.objects.filter(USERID=self.user, notification_type='order').first()
        self.assertIsNotNone(notif_user)
        self.assertIn('has been confirmed', notif_user.notification)

        # Ready for pickup
        response = self.client.post(reverse('Donorrequest'), {
            'request_id': req2.id,
            'status': 'Ready',
            'pickuptime': '12:00:00'
        })
        self.assertEqual(response.status_code, 200)
        
        # Verify user received ready notification
        notif_ready = NotificationTable.objects.filter(USERID=self.user, notification_type='order').order_by('-id').first()
        self.assertIsNotNone(notif_ready)
        self.assertIn('is ready for pickup', notif_ready.notification)

        # 4. Feedback & Complaint replies and notifications
        feedback = FeedbackTable.objects.create(
            feedback='Nice food',
            rating=5,
            USERID=self.user,
            DONORID=self.donor,
            usertype='user'
        )
        complaint = ComplaintTable.objects.create(
            complaint='Late pickup',
            USERID=self.user,
            DONORID=self.donor,
            usertype='donor',
            reply='pending'
        )

        # Donor replies to feedback
        response = self.client.post(reverse('donor_reply_feedback'), {
            'feedback_id': feedback.id,
            'reply': 'Thank you!'
        })
        self.assertEqual(response.status_code, 302)
        feedback.refresh_from_db()
        self.assertEqual(feedback.reply, 'Thank you!')

        # Verify user received feedback reply notification
        notif_fb_reply = NotificationTable.objects.filter(USERID=self.user, notification_type='feedback').first()
        self.assertIsNotNone(notif_fb_reply)
        self.assertIn('replied to your feedback', notif_fb_reply.notification)

        # Donor replies to complaint
        response = self.client.post(reverse('donor_reply_complaint'), {
            'complaint_id': complaint.id,
            'reply': 'Sorry about that'
        })
        self.assertEqual(response.status_code, 302)
        complaint.refresh_from_db()
        self.assertEqual(complaint.reply, 'Sorry about that')

        # Verify user received complaint reply notification
        notif_comp_reply = NotificationTable.objects.filter(USERID=self.user, notification_type='complaint').first()
        self.assertIsNotNone(notif_comp_reply)
        self.assertIn('replied to your complaint', notif_comp_reply.notification)

