from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from listings.models import Listing
from .forms import ReviewForm

# Create your views here.

@login_required
def add_review(request: HttpRequest, l_id: int):
    listing = get_object_or_404(Listing, id=l_id)


    if request.method == "POST":
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.listing = listing
            review.save()
            messages.success(request, "Your review has been submitted!")
            return redirect("listings:load_listing_detail", l_id=l_id)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ReviewForm()
    context = {
        "form": form,
    }

    return render(request, "review_form.html", context=context)