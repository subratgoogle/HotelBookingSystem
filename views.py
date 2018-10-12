from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
from Bookings.models import Status,Feature,Hotel,Customer,Booking,HotelFeature
from .forms import LoginForm, RegistrationForm,BookHotelForm
from django.db import transaction
# Create your views here.
def index(request):
	return render(request, 'booking/index.html')

#function to handle the login operations and load the Login form into the template
def login(request):
	return render(request, 'booking/login.html', {
		'form': LoginForm
	})

#User Registration function to handle the registration Operation by loading the Registration Form into the Registration Template
def register(request):
    return render(request, 'booking/registration.html', {
        'form': RegistrationForm
    })

#Function to handle the data received from the Registration Form
def registration(request):
    if request.method == 'POST':
        customerObj = Customer(name=request.POST['name'],contact=request.POST['contact'],
                               password=request.POST['password'],email=request.POST['email'],
                               address=request.POST['address'])
        customerObj.save()
    return render(request, 'booking/dashboard.html')

#User Dashboard helps to store and validate the data received from the Registration and Login Forms
def dashboard(request):
    if request.method == 'POST':
        name = request.POST['name']
        contact = request.POST['contact']
        password = request.POST['password']
        customerValidate = Customer.objects.filter(contact=contact).exists()
        if not customerValidate:
            return render(request, 'booking/login.html', {
                'form': LoginForm(initial={'contact': contact,'name' :name}, auto_id=False),
                'error_message': 'Your Contact is not registered'
            })
        if Customer.objects.get(contact=contact).password != password :
            return render(request, 'booking/login.html', {
                'form': LoginForm(initial={'contact': contact , 'name' :name}, auto_id=False),
                'error_message': 'Credentials donot match. Please Try Again'
            })
        customerObj = Customer.objects.get(contact=contact)
        request.session['customerPk']=customerObj.pk
        print(request.session)
        return render(request , 'booking/dashboard.html',{'CustName': customerObj.name})


#Function to call and load the Hotel Booking Form into the template
def bookHotel(request):
    return render(request, 'booking/bookHotel.html', {
        'form': BookHotelForm
    })

#Function to handle the data received from the Hotel Booking Form
def bookingResult(request):
    if request.method == 'POST':
        hotelList = list(Hotel.objects.filter(location__iexact=request.POST['location']).values_list('name',flat=True))
        request.session['location'] = request.POST['location']
        if request.POST['amount']:
            request.session['amount']=request.POST['amount']

        if request.POST['checkInDate']:
            request.session['checkInDate'] = request.POST['checkInDate']

        if request.POST['checkOutDate']:
            request.session['checkOutDate'] = request.POST['checkOutDate']

        return render(request, 'booking/hotelList.html', {'hotelList': hotelList})


#function that does the actual Booking by storing the data in the Database. The function is atomic with Rollback Functionality
#so that the booking can be reverted back in case of Connectivity Failure
@transaction.atomic
def bookingConfirmation(request):
    request.session['hotelName']=request.POST['hotelName']
    hotelObj = Hotel.objects.get(name=request.session['hotelName'])
    customerObj = Customer.objects.get(pk=request.session['customerPk'])
    totalCount = hotelObj.visitorCount + 1
    hotelObj.visitorCount = totalCount
    hotelObj.save()
    print(request.POST)
    try:
        if request.POST['Book']:
            bookingObj = Booking(h_id=hotelObj,c_id=customerObj,amount=request.session['amount'],
                                 status=Status.objects.get(status="COMPLETED"),checkInDate=request.session['checkInDate'],
                                 checkOutDate=request.session['checkOutDate'])
            bookingObj.save()
            return HttpResponse('Your Booking has been Successfully Done')
    except :
        bookingObj = Booking(h_id=hotelObj, c_id=customerObj, amount=request.session['amount'],
                             status=Status.objects.get(status="DROPPED"), checkInDate=request.session['checkInDate'],
                             checkOutDate=request.session['checkOutDate'])
        bookingObj.save()
        return HttpResponse('Your Booking has been Successfully Saved In the Drafts')



#to check the number of visits to a particular hotel
def viewVisits(request):
    hotelList = Hotel.objects.all()
    return render(request,'booking/viewVisit.html',{'hotelList': hotelList})

#function provides the data for displaying the draft Booking Functionality
def draftBooking(request):
    print(request.session['customerPk'])
    bookingListObj = list(Booking.objects.filter(status=Status.objects.get(status="DROPPED"))
                          .filter(c_id=request.session['customerPk']))
    print(bookingListObj)
    if len(bookingListObj) == 0:
        return HttpResponse("No Draft Bookings To Display")
    return render(request, 'booking/draftBooking.html',{'bookingListObj':bookingListObj})