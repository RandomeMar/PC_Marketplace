from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from listings.models import Listing, Message

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}!')
            return redirect('homepage')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('homepage')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out.')
    return redirect('homepage')

@login_required
def profile_view(request, username=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
        is_own_profile = request.user == profile_user
    else:
        profile_user = request.user
        is_own_profile = True
    
    listings = Listing.objects.filter(owner=profile_user, status='active').order_by('-upload_time')
    
    has_conversation = False
    if request.user.is_authenticated and not is_own_profile:
        has_conversation = Message.objects.filter(
            sender__in=[request.user, profile_user],
            receiver__in=[request.user, profile_user]).exists()
    
    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'listings': listings,
        'has_conversation': has_conversation,
    }
    
    return render(request, 'accounts/profile.html', context)
