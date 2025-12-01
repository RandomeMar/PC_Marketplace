from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, Http404
from django.apps import apps
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Min, Max, Model, Q, QuerySet
from django.db.models import Avg, Count
from products.models import Product
from .models import Listing, ListingImage, Message
from .forms import ListingForm, ListingImageFormSet
from urllib.parse import unquote
from rapidfuzz import process, fuzz
from reviews.models import Review
from django.contrib.auth.models import User
from .models import Purchase


# Create your views here.

def test(request: HttpRequest):
    """
    Returns a "TESTING" message to the webpage. 
    """
    return HttpResponse("TESTING")

def homepage(request: HttpRequest):
    """
    Renders homepage.html template.
    """
    print("test")
    return render(request, "homepage.html") 


def select_p_type(request: HttpRequest, next_url="search/"):
    """
    Loads page for selecting a product type.
    
    Args:
        request (HttpRequest): Incoming HTTP request.
        next_url (str): URL that will be loaded after the form has been
            submitted.
    
    Returns:
        HttpResponse: The rendered "select_p_type.html" template with
            a selected next URL.
    """
    options = [{"value": p_type.__name__, "name": p_type._meta.verbose_name_plural} for p_type in Product.__subclasses__()]
    context = {
        "next_url": next_url,
        "options": options,
    }
    return render(request, "select_p_type.html", context=context)

def fuzzy_search(qs: QuerySet, query: str, choice_field: str, score_cutoff=60):
    """
    Performs a fuzzy search.
    
    Args:
        qs (QuerySet): Queryset that fuzzy_search will get choices from.
        query (str): Query to be matched against.
        choice_field (str): Field in qs to be compared against the query.
        score_cutoff (int): Minimum value score to appear in matched_records.
    Returns:
        list[Model]: A list of records that most closely match the query.
    """
    
    if not qs:
        return []
    
    temp = qs.values_list("id", choice_field)
    ids, choices = zip(*[(id, name.lower().strip()) for id, name in temp])
    
    if not query:
        return list(qs)
    
    matches = process.extract(query, choices, scorer=lambda q, c, score_cutoff=score_cutoff: max(
            fuzz.token_set_ratio(q, c, score_cutoff=score_cutoff),
            fuzz.partial_ratio(q, c, score_cutoff=score_cutoff)
        ),
        limit=30
    )
    
    matched_ids = [ids[match[2]] for match in matches]
    matched_records: list[Model] = list(qs.filter(id__in=matched_ids))
    matched_records.sort(key=lambda p: matched_ids.index(p.id)) # Sorts queryset by match score since querysets don't preserve order
    return matched_records


def search_listings(request: HttpRequest, p_type: str):
    """
    Handles searching for listings.
    
    This view expects a 'q' query parameter and other filters in the
    URL. It loads the proper Product subclass, performs a fuzzy search 
    on listings of the subclass, and renders the search results.
    
    Args:
        request (HttpRequest): Incoming HTTP request. May include query
            parameters like 'q' and other filters.
        p_type (str): The name of a model class in the "products" app 
            that represents a subclass of Product.
    
    Returns:
        HttpResponse: The rendered "listing_search.html" template with
            search results based on the query and set filters.
    
    Raises:
        ValueError: If "p_type" does not match any subclass of Product.
    """
    product_model: type[Product] = load_product_model(p_type)
    
    l_filter_vals = gather_filters(request, Listing)
    p_filter_vals = gather_filters(request, product_model, "product__")
    
    query = request.GET.get("q")
    if query:
        query = unquote(query)
    
    filtered_listings = Listing.objects.filter(
        **{f"product__{product_model.__name__.lower()}__isnull": False},
        **l_filter_vals["str"], **l_filter_vals["int"], **l_filter_vals["bool"],
        **p_filter_vals["str"], **p_filter_vals["int"], **p_filter_vals["bool"],
        )
    
    
    
    matched_listings = fuzzy_search(filtered_listings, query, "title")
    
    l_filter_fields = build_filter_fields(Listing, l_filter_vals)
    p_filter_fields = build_filter_fields(product_model, p_filter_vals, "product__")
    
    context = {
        "p_type": p_type,
        "listings": matched_listings,
        "query": query,
        "l_filter_fields": l_filter_fields,
        "p_filter_fields": p_filter_fields,
    }
    
    return render(request, "search_listings.html", context)


def load_product_model(product_type_str: str):
    """
    Loads a Django product model class by name or raises a value error.
    
    Args:
        product_type_str (str): The name of a model class in the
            "products" app that should represent a subclass of Product.
    
    Returns:
        type[Product]: The corresponding Product subclass.
    
    Raises:
        ValueError: If the input string does not represent a subclass of
            Product.
    """
    product_model = apps.get_model("products", product_type_str)
    if not issubclass(product_model, Product):
        # TODO: We may want to just load a different page instead of raising a value error.
        raise ValueError(f"{product_type_str} is not a Product subclass")
    return product_model

def gather_filters(request: HttpRequest, model: type[Model], prefix="") -> dict:
    """
    Creates a filter values dict for a model from an http GET request.
    
    This dict can be directly used to filter a model through **dict notation.
    
    Args:
        request: Contains filters values.
        model: Model to get filters from.
        prefix: Used when accessing filters from a foreign key.
    
    Returns:
        dict: Filter values.
    """
    str_filters = {}
    int_filters = {}
    float_filters = {}
    bool_filters = {}
    
    # Gets filter values from GET.
    for field in model._meta.get_fields():
        if not field.concrete or field.is_relation:
            continue
        if field.get_internal_type() == "PositiveIntegerField":
            # Integer field
            min_val = request.GET.get(f"{field.name}_min")
            max_val = request.GET.get(f"{field.name}_max")
            
            try:
                if min_val is None or min_val == "":
                    raise ValueError
                int_filters[f"{prefix}{field.name}__gte"] = int(min_val)
            except ValueError:
                pass
            try:
                if max_val is None or max_val == "":
                    raise ValueError
                int_filters[f"{prefix}{field.name}__lte"] = int(max_val)
            except ValueError:
                pass
        
        elif field.get_internal_type() == "FloatField":
            # Float/Decimal field
            min_val = request.GET.get(f"{field.name}_min")
            max_val = request.GET.get(f"{field.name}_max")
            
            
            try:
                if min_val is None or min_val == "":
                    raise ValueError
                float_filters[f"{prefix}{field.name}__gte"] = float(min_val)
            except ValueError:
                pass
            try:
                if max_val is None or max_val == "":
                    raise ValueError
                float_filters[f"{prefix}{field.name}__lte"] = float(max_val)
            except ValueError:
                pass
        
        elif field.get_internal_type() == "BooleanField":
            # Boolean field
            value = request.GET.get(field.name)
            if value == "True":
                bool_filters[f"{prefix}{field.name}"] = True
            elif value == "False":
                bool_filters[f"{prefix}{field.name}"] = False
        
        else:
            # String field
            values = request.GET.getlist(field.name)
            if values:
                str_filters[f"{prefix}{field.name}__in"] = values
        
                
    return {"str": str_filters, "int": int_filters, "float": float_filters, "bool": bool_filters}

def build_filter_fields(model: type[Model], filter_vals: dict[dict], prefix="") -> dict[dict]:
    """
    Creates a dict storing filter fields for templates.
    
    Args:
        model: Model fields are from.
        filter_vals: Dict containing filter values. See gather_filters().
        prefix: Used when accessing filters of a foreign key.
    Returns:
        dict: This nested dict contains filters of different data types.
            The structure of each data type is different so read carefully
            to know how to implement a template with it.
    """
    str_options = {}
    int_options = {}
    float_options = {}
    bool_options = {}
    
    # Gets filter fields with options for the template.
    for field in model._meta.get_fields():
        if not field.concrete or field.is_relation:
            continue
        if field.name not in getattr(model, "FILTER_FIELDS", []):
            continue
        
        if field.get_internal_type() == "PositiveIntegerField":
            # Get int field options     
            
            min_max = model.objects.aggregate(
                min_val=Min(field.name),
                max_val=Max(field.name)
                )
            int_options[field.name] = {
                "label": field.verbose_name,
                "min_val": min_max["min_val"],
                "max_val": min_max["max_val"],
            }
            if filter_vals["int"].get(f"{prefix}{field.name}__gte"):
                int_options[field.name]["user_min"] = filter_vals["int"][
                    f"{prefix}{field.name}__gte"]
            if filter_vals["int"].get(f"{prefix}{field.name}__lte"):
                int_options[field.name]["user_max"] = filter_vals["int"][
                    f"{prefix}{field.name}__lte"]
        
        elif field.get_internal_type() == "FloatField":
            # Get float field options
            min_max = model.objects.aggregate(
                min_val=Min(field.name),
                max_val=Max(field.name)
                )
            float_options[field.name] = {
                "label": field.verbose_name,
                "min_val": min_max["min_val"],
                "max_val": min_max["max_val"],
            }
            if filter_vals["float"].get(f"{prefix}{field.name}__gte"):
                float_options[field.name]["user_min"] = filter_vals["float"][
                    f"{prefix}{field.name}__gte"]
            if filter_vals["float"].get(f"{prefix}{field.name}__lte"):
                float_options[field.name]["user_max"] = filter_vals["float"][
                    f"{prefix}{field.name}__lte"]
        
        elif field.get_internal_type() == "BooleanField":
            # Get bool field options
            bool_options[field.name] = {
                "label": field.verbose_name,
                "user_input": filter_vals["bool"].get(f"{prefix}{field.name}")
            }
        
        else:
            # Get string field options
            options = model.objects.values_list(field.name, flat=True).distinct().order_by(field.name)
            str_options[field.name] = {
                "label": field.verbose_name, 
                "options": options,
                "user_inputs": filter_vals["str"].get(f"{prefix}{field.name}__in")
                }
    return {
        "str": str_options, "int": int_options, "float": float_options,
        "bool": bool_options
        }

def search_products(request: HttpRequest, p_type: str):
    """
    Handles searching for products when creating a listing.
    
    This view expects a 'q' query parameter and other filters in the
    URL. It loads the proper Product subclass, performs a fuzzy search 
    on the subclass, and renders the search results.
    
    Args:
        request (HttpRequest): Incoming HTTP request. May include query
            parameters like 'q' and other filters.
        p_type (str): The name of a model class in the "products" app 
            that represents a subclass of Product.
    
    Returns:
        HttpResponse: The rendered "product_search.html" template with
            search results based on the query and set filters.
    
    Raises:
        ValueError: If "p_type" does not match any subclass of Product.
    """
    product_model: type[Product] = load_product_model(p_type)
    filter_vals = gather_filters(request, product_model)
    
    query = request.GET.get("q")
    if query:
        query = unquote(query)
    
    filtered_products: QuerySet = product_model.objects.filter(
        **filter_vals["str"],
        **filter_vals["int"],
        **filter_vals["bool"],
        **filter_vals["float"],
        )
    
    matched_products = fuzzy_search(filtered_products, query, "product_name")
    
    filter_fields = build_filter_fields(product_model, filter_vals)
    
    
    context = {
        "p_type": p_type,
        "products": matched_products,
        "query": query,
        "filter_fields": filter_fields,
    }
    
    return render(request, "search_products.html", context)


@login_required
def create_listing(request: HttpRequest, p_type: str, p_id: int):
    """
    Handles creating listings based off a given product.
    
    This view processes a listing creation form submitted via a POST
    request. If it receives a valid form, a new Listing record is added,
    and it redirects to the new listing's page. If the form is invalid
    or not provided, the form is re-rendered.
    
    Args:
        request (HttpRequest): Incoming HTTP request. Contains form data.
        p_type (str): The name of a model class in the "products" app 
            that represents a subclass of Product.
        p_id (int): The ID of the product the listing is based on.
    Returns:
        HttpResponse: Renders the "listing_form.html" template if the
            form is invalid or missing. Redirects to the
            "load_listing_detail" view if the form submission is valid.
    """
    if request.method == "POST":
        form = ListingForm(request.POST)
        image_formset = ListingImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and image_formset.is_valid():
            listing = form.save(commit=False)
            listing.product_id = p_id
            listing.owner = request.user

            listing.save()
            
            # Save images
            images = image_formset.save(commit=False)
            for idx, image in enumerate(images):
                if image.image:
                    image.listing = listing
                    image.order = idx
                    image.save()
            
            messages.success(request, "Listing created successfully!")
            return redirect("listings:load_listing_detail", l_id=listing.id)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ListingForm()
        image_formset = ListingImageFormSet()
    
    context = {
        "form": form,
        "image_formset": image_formset,
    }
    
    return render(request, "create_listing.html", context=context)


def load_listing_detail(request: HttpRequest, l_id: int):
    """
    Loads the listing page of the provided listing ID.
    
    Args:
        request (HttpRequest): Incoming HTTP request.
        l_id (int): The ID of the listing.
    
    Returns:
        HttpResponse: Renders template "listing_detail.html" using the
            provided listing.
    
    Raises:
        Http404: If there is no listing with the provided ID.
    """
    listing = get_object_or_404(Listing, id=l_id)
    images = listing.images.all()
    
    is_owner: bool = listing.owner == request.user
    user_has_reviewed = False
    if not is_owner and request.user.is_authenticated:
        user_has_reviewed: bool = Review.objects.filter(reviewer=request.user, listing=listing).exists()
    
    context = {
        "listing": listing,
        "images": images,
        "is_owner": is_owner,
        "user_has_reviewed": user_has_reviewed
    }
    
    return render(request, "listing_detail.html", context=context)


@login_required
def edit_listing(request: HttpRequest, l_id: int):
    """
    Allows the owner to edit their listing.
    
    Args:
        request (HttpRequest): Incoming HTTP request.
        l_id (int): The ID of the listing to edit.
    
    Returns:
        HttpResponse: Renders the listing edit form or redirects after saving.
    
    Raises:
        Http404: If the listing doesn't exist or user doesn't own it.
    """
    listing = get_object_or_404(Listing, id=l_id, owner=request.user)
    
    if request.method == "POST":
        form = ListingForm(request.POST, instance=listing)
        image_formset = ListingImageFormSet(request.POST, request.FILES, instance=listing)
        
        if form.is_valid() and image_formset.is_valid():
            form.save()
            
            # Save images
            images = image_formset.save(commit=False)
            for idx, image in enumerate(images):
                if image.image:
                    image.order = idx
                    image.save()
            
            #deleted images
            for image in image_formset.deleted_objects:
                image.delete()
            
            messages.success(request, "Listing updated successfully!")
            return redirect("listings:load_listing_detail", l_id=listing.id)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ListingForm(instance=listing)
        image_formset = ListingImageFormSet(instance=listing)
    
    context = {
        "form": form,
        "image_formset": image_formset,
        "listing": listing,
        "is_edit": True,
    }

    return render(request, "create_listing.html", context=context)


@login_required
@require_POST
def delete_listing(request: HttpRequest, l_id: int):
    """
    Allows the owner to delete their listing.
    
    Args:
        request (HttpRequest): Incoming HTTP request.
        l_id (int): The ID of the listing to delete.
    
    Returns:
        HttpResponse: Confirmation page or redirect after deletion.
    
    Raises:
        Http404: If the listing doesn't exist, the user doesn't own it,
            or the page was loaded with GET.
    """
    listing = get_object_or_404(Listing, id=l_id, owner=request.user)
    listing.delete()
    messages.success(request, "Listing deleted successfully!")

    next = request.POST.get("next")
    if not next:
        next = "listings:my_listings"
    return redirect(next)


@login_required
def my_listings(request: HttpRequest):
    """
    Shows all listings created by the current user.
    
    Args:
        request (HttpRequest): Incoming HTTP request.
    
    Returns:
        HttpResponse: Renders page showing user's listings.
    """
    listings = Listing.objects.filter(owner=request.user).order_by('-upload_time')
    
    context = {
        "listings": listings,
    }

    return render(request, "my_listings.html", context=context)


def all_listings_page(request: HttpRequest):
    """
    Shows all active listings (public marketplace view).
    
    Args:
        request (HttpRequest): Incoming HTTP request.
    
    Returns:
        HttpResponse: Renders page showing all active listings.
    """
    # Get filter parameters
    query = request.GET.get('q', '')
    condition = request.GET.get('condition', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    listings = Listing.objects.filter(status='active').annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews', distinct=True)
    )
    
    # applies filters
    if query:
        listings = listings.filter(
            Q(title__icontains=query) | 
            Q(listing_text__icontains=query)
        )
    
    if condition:
        listings = listings.filter(condition=condition)
    
    if min_price:
        try:
            listings = listings.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            listings = listings.filter(price__lte=float(max_price))
        except ValueError:
            pass
        
    context = {
        "listings": listings,
        "query": query,
        "condition": condition,
        "min_price": min_price,
        "max_price": max_price,
        "condition_choices": Listing.CONDITION_CHOICES,
    }
    
    return render(request, "all_listings_page.html", context=context)


# Chat System
@login_required
def inbox(request):
    sent_messages = Message.objects.filter(sender=request.user).values('receiver', 'listing').distinct()
    received_messages = Message.objects.filter(receiver=request.user).values('sender', 'listing').distinct()
    
    conversations = []
    seen = set()
    
    for msg in sent_messages:
        other_user_id = msg['receiver']
        listing_id = msg['listing']
        if listing_id:  # Only show specific listing chat rooms
            key = (other_user_id, listing_id)
            if key not in seen:
                other_user = User.objects.get(id=other_user_id)
                listing = Listing.objects.get(id=listing_id)
                conversations.append({'user': other_user,'listing': listing,'listing_id': listing_id})
                seen.add(key)
    
    for msg in received_messages:
        other_user_id = msg['sender']
        listing_id = msg['listing']
        if listing_id:
            key = (other_user_id, listing_id)
            if key not in seen:
                other_user = User.objects.get(id=other_user_id)
                listing = Listing.objects.get(id=listing_id)
                conversations.append({
                    'user': other_user,
                    'listing': listing,
                    'listing_id': listing_id
                })
                seen.add(key)
    
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    
    return render(request, 'chat/inbox.html', {
        'conversations': conversations,
        'unread_count': unread_count
    })


@login_required
def conversation(request, user_id, listing_id):
    other_user = get_object_or_404(User, id=user_id)
    listing = get_object_or_404(Listing, id=listing_id)
    
    #Get messages between these two users about a specific listing
    messages = Message.objects.filter(sender__in=[request.user, other_user],receiver__in=[request.user, other_user],listing=listing).order_by('timestamp')
    
    #marks message as read
    Message.objects.filter(sender=other_user, receiver=request.user, listing=listing,is_read=False).update(is_read=True)

    room_name = f"{min(request.user.id, other_user.id)}_{max(request.user.id, other_user.id)}_listing_{listing.id}"
    return render(request, 'chat/data.html', { 'other_user': other_user, 'messages': messages,'room_name': room_name,'listing': listing,})


@login_required
def contact_seller(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    seller = listing.owner
    
    if request.user == seller:
        return redirect('listings:load_listing_detail', l_id=listing_id)
    
    if request.method == 'POST':
        message_text = request.POST.get('message_text')
        if message_text:
            Message.objects.create( sender=request.user, receiver=seller, listing=listing, message_text=message_text)
            return redirect('listings:data_listing', user_id=seller.id, listing_id=listing_id) #returns to specific listing now
    
    return render(request, 'chat/message.html', {
        'listing': listing,
        'seller': seller
    })


#Purchase Views
@login_required
def create_purchase(request, listing_id, user_id):
    listing = get_object_or_404(Listing, id=listing_id)
    other_user = get_object_or_404(User, id=user_id)
    
    #check to see who's who
    if request.user == listing.owner:
        seller = request.user
        buyer = other_user
    else:
        buyer = request.user
        seller = listing.owner
    
    if request.method == 'POST':
        agreed_price = request.POST.get('agreed_price')
        meetup_location = request.POST.get('meetup_location')
        meetup_datetime = request.POST.get('meetup_date') + ' ' + request.POST.get('meetup_time')
        
        from django.utils.dateparse import parse_datetime
        meetup_time = parse_datetime(meetup_datetime)
        
        purchase = Purchase.objects.create( listing=listing, seller=seller, buyer=buyer, agreed_price=agreed_price, meetup_location=meetup_location,
            meetup_time=meetup_time, buyer_confirmation=(request.user == buyer), seller_confirmation=(request.user == seller))
        
        Message.objects.create( sender=request.user, receiver=other_user, listing=listing,
            message_text=f"📋 Purchase Proposal: ${agreed_price} | Meetup: {meetup_location} on {meetup_time.strftime('%b %d, %Y at %I:%M %p')}")
        
        messages.success(request, 'Purchase proposal sent!')
        return redirect('listings:data_listing', user_id=other_user.id, listing_id=listing_id)
    
    return render(request, 'chat/create_purchase.html', { 'listing': listing, 'other_user': other_user,})


@login_required
def confirm_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if request.user not in [purchase.buyer, purchase.seller]:
        messages.error(request, 'You are not part of this purchase.')
        return redirect('homepage')
    
    if request.user == purchase.buyer:
        purchase.buyer_confirmation = True
    else:
        purchase.seller_confirmation = True
    
    purchase.save()
    
    if purchase.buyer_confirmation and purchase.seller_confirmation:
        purchase.status = 'complete'
        purchase.save()
    
    other_user = purchase.seller if request.user == purchase.buyer else purchase.buyer
    Message.objects.create( sender=request.user, receiver=other_user, listing=purchase.listing, message_text=f"{request.user.username} confirmed the purchase!")
    
    if purchase.status == 'complete':
        messages.success(request, 'Both parties confirmed! Purchase complete.')
    else:
        messages.success(request, 'You confirmed the purchase. Waiting for other party.')
    
    return redirect('listings:data_listing', user_id=other_user.id, listing_id=purchase.listing.id)


@login_required
def cancel_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if request.user not in [purchase.buyer, purchase.seller]:
        messages.error(request, 'You cannot cancel this purchase.')
        return redirect('homepage')
    
    purchase.status = 'cancelled'
    purchase.save()
    
    other_user = purchase.seller if request.user == purchase.buyer else purchase.buyer
    Message.objects.create(
        sender=request.user,
        receiver=other_user,
        listing=purchase.listing,
        message_text=f"{request.user.username} cancelled the purchase."
    )
    
    messages.info(request, 'Purchase cancelled.')
    return redirect('listings:data_listing', user_id=other_user.id, listing_id=purchase.listing.id)


@login_required
def view_purchases(request):
    buying = Purchase.objects.filter(buyer=request.user).order_by('-timestamp')
    selling = Purchase.objects.filter(seller=request.user).order_by('-timestamp')
    
    return render(request, 'chat/purchases.html', {
        'buying': buying,
        'selling': selling,
    })