from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Product, Season, Occasion, Category, UserProfile, Cart, CartItem, Order, OrderItem
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import datetime
import json

# ... (landing, seasonal_mart, shop views remain same)

def landing(request):
    """Render the main landing page (Regular mode)."""
    # Fetch featured products or just all products for now
    featured_products = Product.objects.filter(available=True)[:8]
    context = {
        'products': featured_products,
        'mode': 'regular'
    }
    return render(request, 'FestivMartApp/landing.html', context)

def seasonal_mart(request):
    """Render the seasonal shopping page."""
    today = timezone.now().date()
    
    # Active Seasons
    active_seasons = Season.objects.filter(start_date__lte=today, end_date__gte=today)
    
    # Active/Upcoming Occasions (next 60 days)
    upcoming_occasions = Occasion.objects.filter(date__gte=today, date__lte=today + datetime.timedelta(days=60))
    
    # Get categories for filtering
    categories = Category.objects.all()

    # Get seasonal products
    products = Product.objects.filter(is_seasonal=True, available=True)
    
    # If we have active seasons or upcoming occasions, filter by them
    if active_seasons.exists() or upcoming_occasions.exists():
        products = products.filter(
            Q(season__in=active_seasons) | Q(occasions__in=upcoming_occasions)
        ).distinct()
    
    # If no products match, show all available seasonal products
    if not products.exists():
        products = Product.objects.filter(is_seasonal=True, available=True)[:12]
    
    # If still no products, show latest available products
    if not products.exists():
        products = Product.objects.filter(available=True).order_by('-id')[:12]

    context = {
        'products': products,
        'seasons': active_seasons,
        'occasions': upcoming_occasions,
        'categories': categories,
        'mode': 'seasonal'
    }
    return render(request, 'FestivMartApp/seasonal-mart.html', context)

@login_required
def dashboard(request):
    """Render the user dashboard with shopping insights."""
    user = request.user
    is_business = False
    my_products = []
    
    if hasattr(user, 'profile') and user.profile.is_business:
        is_business = True
        my_products = Product.objects.filter(seller=user)
        
    # Calculate stats for the score cards
    today = timezone.now()
    member_since = user.date_joined
    account_age_days = (today - member_since).days
    
    total_products = my_products.count() if is_business else 0
    seasonal_products = my_products.filter(is_seasonal=True).count() if is_business else 0
    
    # Points logic (consistent with score_view)
    points = (account_age_days * 5) + (total_products * 50) + (seasonal_products * 20)
    level = (points // 500) + 1
    next_level_points = (level * 500) - points
    progress_percentage = (points % 500) / 500 * 100
    
    # For the CIBIL style gauge in score.html (0-900 scale)
    # We can map our points to 900
    gauge_score = min(740 + (points // 10), 900) # Start from 740 for demo feel or scale differently
    
    context = {
        'is_business': is_business,
        'my_products': my_products,
        'stats': {
            'member_since': member_since.strftime('%B %Y'),
            'account_age_days': account_age_days,
            'total_products': total_products,
            'seasonal_products': seasonal_products,
            'total_orders': 0,
        },
        'score_data': {
            'points': points,
            'gauge_score': gauge_score,
            'level': level,
            'next_level_points': next_level_points,
            'progress_percentage': progress_percentage,
        }
    }
    return render(request, 'FestivMartApp/dashboard.html', context)

def shop(request):
    """Render the full shop page."""
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories
    }
    return render(request, 'FestivMartApp/shop.html', context)

@login_required
def add_product(request):
    """View for sellers to add new products."""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_business:
        return redirect('dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        is_seasonal = request.POST.get('is_seasonal') == 'on'
        image = request.FILES.get('image')
        image_url = request.POST.get('image_url', '').strip()
        stock = request.POST.get('stock', 1)
        discount = request.POST.get('discount', 0)
        
        try:
            stock = int(stock)
        except (ValueError, TypeError):
            stock = 1
            
        try:
            discount = int(discount)
        except (ValueError, TypeError):
            discount = 0
        
        category = get_object_or_404(Category, id=category_id)
        
        product = Product.objects.create(
            name=name,
            price=price,
            category=category,
            description=description,
            is_seasonal=is_seasonal,
            seller=request.user,
            image=image if image else None,
            image_url=image_url if image_url and not image else None,
            stock=stock,
            discount_percent=discount
        )
        # Handle seasons/occasions if seasonal logic needed here
        return redirect('dashboard')
        
    categories = Category.objects.all()
    return render(request, 'FestivMartApp/add_product.html', {'categories': categories})


def get_or_create_cart(request):
    """Helper function to get or create a cart for the current user/session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For anonymous users, use session
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart


def cart(request):
    """Render the cart page with items from database."""
    cart_obj = get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('product').all()
    
    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
    }
    return render(request, 'FestivMartApp/cart.html', context)


@login_required
def checkout(request):
    """Handle checkout and order creation."""
    cart_obj = get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('product').all()
    
    if not cart_items.exists():
        return redirect('cart')
    
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        payment_method = request.POST.get('payment_method', 'cod')
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            postal_code=postal_code,
            subtotal=cart_obj.subtotal,
            discount_amount=cart_obj.discount_amount,
            tax_amount=cart_obj.tax_amount,
            shipping_cost=cart_obj.shipping_cost,
            total=cart_obj.total,
            coupon_code=cart_obj.coupon_code,
            payment_method=payment_method,
        )
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total,
            )
            # Reduce stock
            item.product.stock -= item.quantity
            item.product.save()
        
        # Clear the cart
        cart_obj.clear()
        
        # Redirect to success page
        return redirect('order_success', order_number=order.order_number)
    
    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
    }
    return render(request, 'FestivMartApp/checkout.html', context)

def login_view(request):
    """View to handle user login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # In this project, we might be using email as username or just username.
        # Let's check if the user exists with this email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            username = email # Fallback to using email as username
            
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'FestivMartApp/login.html', {'error': 'Invalid credentials'})
            
    return render(request, 'FestivMartApp/login.html')

def logout_view(request):
    """View to handle user logout."""
    logout(request)
    return redirect('home')

def signup_view(request):
    """View to handle user signup."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        account_type = request.POST.get('account_type', 'individual')
        is_business = account_type == 'business'
        business_name = request.POST.get('business_name', '')
        
        # Validate passwords match
        if password != password_confirm:
            return render(request, 'FestivMartApp/signup.html', {'error': 'Passwords do not match'})
        
        if not username or not email or not password:
            return render(request, 'FestivMartApp/signup.html', {'error': 'Please fill in all required fields'})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'FestivMartApp/signup.html', {'error': 'Username already exists'})
        
        if User.objects.filter(email=email).exists():
            return render(request, 'FestivMartApp/signup.html', {'error': 'Email already exists'})
            
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create Profile
        UserProfile.objects.get_or_create(
            user=user, 
            defaults={
                'is_business': is_business,
                'business_name': business_name if is_business else ''
            }
        )
        
        login(request, user)
        return redirect('dashboard')
        
    return render(request, 'FestivMartApp/signup.html')


@login_required
def score_view(request):
    """View to display user's activity score and statistics."""
    user = request.user
    is_business = False
    if hasattr(user, 'profile'):
        is_business = user.profile.is_business
    
    # Calculate stats
    today = timezone.now()
    member_since = user.date_joined
    account_age_days = (today - member_since).days
    
    total_products = 0
    seasonal_products = 0
    if is_business:
        my_products = Product.objects.filter(seller=user)
        total_products = my_products.count()
        seasonal_products = my_products.filter(is_seasonal=True).count()
    
    # Points logic (Simplified for demo)
    points = (account_age_days * 5) + (total_products * 50) + (seasonal_products * 20)
    level = (points // 500) + 1
    next_level_points = (level * 500) - points
    progress_percentage = (points % 500) / 500 * 100
    
    badges = []
    if account_age_days > 7:
        badges.append({'name': 'Early Adopter', 'icon': '🌟', 'color': '#FF6B35'})
    if total_products > 0:
        badges.append({'name': 'First Listing', 'icon': '📦', 'color': '#7C3AED'})
    if total_products >= 5:
        badges.append({'name': 'Pro Seller', 'icon': '🚀', 'color': '#FBBF24'})
        
    context = {
        'is_business': is_business,
        'stats': {
            'member_since': member_since.strftime('%B %Y'),
            'account_age_days': account_age_days,
            'total_products': total_products,
            'seasonal_products': seasonal_products,
            'total_orders': 0, # Placeholder
        },
        'score_data': {
            'points': points,
            'level': level,
            'next_level_points': next_level_points,
            'progress_percentage': progress_percentage,
            'badges': badges
        }
    }
    return render(request, 'FestivMartApp/score.html', context)

def year_dates_api(request):
    """
    API to fetch the entire year dates and occasional days.
    """
    current_year = timezone.now().year
    
    # Fetch all seasons and occasions
    seasons = Season.objects.all().values('name', 'start_date', 'end_date', 'description')
    occasions = Occasion.objects.all().values('name', 'date', 'description')
    
    data = {
        'year': current_year,
        'seasons': list(seasons),
        'occasions': list(occasions)
    }
    
    return JsonResponse(data)


def product_detail_api(request, product_id):
    """API to get detailed product info and related products."""
    product = get_object_or_404(Product, id=product_id)
    
    # Related products: same category, exclude current, limit 4
    related = Product.objects.filter(category=product.category, available=True).exclude(id=product.id)[:4]
    
    related_data = []
    for p in related:
        related_data.append({
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'discounted_price': float(p.discounted_price),
            'image': p.get_image_url(),
            'discount_percent': p.discount_percent
        })
        
    data = {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': float(product.price),
        'discounted_price': float(product.discounted_price),
        'discount_percent': product.discount_percent,
        'image': product.get_image_url(),
        'stock': product.stock,
        'category': str(product.category),
        
        # Mock/Calculated data features
        'rating': 4.5, 
        'reviews_count': 42 + product.id,
        'total_buys': 120 + product.id * 5, 
        'return_policy': '7 Days Return & Exchange',
        'is_in_stock': product.is_in_stock,
        
        'related_products': related_data
    }
    return JsonResponse(data)


# ============== CART API VIEWS ==============

@csrf_exempt
def cart_add(request):
    """API to add item to cart."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
    
    product = get_object_or_404(Product, id=product_id, available=True)
    cart = get_or_create_cart(request)
    
    # Check if item already in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'message': f'{product.name} added to cart',
        'cart_count': cart.item_count,
        'cart_total': float(cart.total),
    })


@csrf_exempt
def cart_update(request):
    """API to update cart item quantity."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
    
    cart = get_or_create_cart(request)
    
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
    
    if quantity <= 0:
        cart_item.delete()
        message = 'Item removed from cart'
    else:
        cart_item.quantity = quantity
        cart_item.save()
        message = 'Cart updated'
    
    return JsonResponse({
        'success': True,
        'message': message,
        'cart_count': cart.item_count,
        'subtotal': float(cart.subtotal),
        'discount': float(cart.discount_amount),
        'tax': float(cart.tax_amount),
        'shipping': float(cart.shipping_cost),
        'total': float(cart.total),
    })


@csrf_exempt
def cart_remove(request):
    """API to remove item from cart."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
    
    cart = get_or_create_cart(request)
    
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
    
    return JsonResponse({
        'success': True,
        'message': 'Item removed',
        'cart_count': cart.item_count,
        'subtotal': float(cart.subtotal),
        'discount': float(cart.discount_amount),
        'tax': float(cart.tax_amount),
        'shipping': float(cart.shipping_cost),
        'total': float(cart.total),
    })


@csrf_exempt
def cart_apply_coupon(request):
    """API to apply coupon code."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
    
    cart = get_or_create_cart(request)
    success, message = cart.apply_coupon(code)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'discount_percent': cart.discount_percent,
        'subtotal': float(cart.subtotal),
        'discount': float(cart.discount_amount),
        'tax': float(cart.tax_amount),
        'shipping': float(cart.shipping_cost),
        'total': float(cart.total),
    })


def cart_data(request):
    """API to get cart data for JS."""
    cart = get_or_create_cart(request)
    
    items = []
    for item in cart.items.select_related('product', 'product__category').all():
        items.append({
            'id': item.id,
            'product_id': item.product.id,
            'name': item.product.name,
            'category': item.product.category.name if item.product.category else '',
            'image': item.product.get_image_url(),
            'price': float(item.unit_price),
            'original_price': float(item.product.price),
            'quantity': item.quantity,
            'line_total': float(item.line_total),
        })
    
    return JsonResponse({
        'success': True,
        'items': items,
        'cart_count': cart.item_count,
        'coupon_code': cart.coupon_code or '',
        'discount_percent': cart.discount_percent,
        'subtotal': float(cart.subtotal),
        'discount': float(cart.discount_amount),
        'tax': float(cart.tax_amount),
        'shipping': float(cart.shipping_cost),
        'total': float(cart.total),
    })


@login_required
def order_success(request, order_number):
    """Display order success page."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'FestivMartApp/order_success.html', context)

