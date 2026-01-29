from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Product, Category
from .forms import SignupForm


def index(request):
	products = Product.objects.filter(is_active=True).order_by('-created_at')[:12]
	categories = Category.objects.all()
	return render(request, 'landing.html', {'products': products, 'categories': categories})


def product_list(request, category_slug=None):
	qs = Product.objects.filter(is_active=True)
	category = None
	if category_slug:
		category = get_object_or_404(Category, slug=category_slug)
		qs = qs.filter(category=category)
	return render(request, 'landing.html', {'products': qs, 'categories': Category.objects.all(), 'current_category': category})


def product_detail(request, slug):
	product = get_object_or_404(Product, slug=slug, is_active=True)
	return render(request, 'product_detail.html', {'product': product})


def signup_view(request):
	if request.method == 'POST':
		# Try using the form first (if template provides standard fields)
		form = SignupForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('dashboard')

		# Fallback: template may post `email`, `password`, and `fullname` fields
		email = request.POST.get('email')
		password = request.POST.get('password')
		fullname = request.POST.get('fullname') or request.POST.get('name')
		if email and password:
			from django.contrib.auth.models import User
			username = email.split('@')[0]
			# Ensure username uniqueness
			base = username
			i = 1
			while User.objects.filter(username=username).exists():
				username = f"{base}{i}"
				i += 1
			user = User.objects.create_user(username=username, email=email, password=password)
			if fullname:
				parts = fullname.split(None, 1)
				user.first_name = parts[0]
				if len(parts) > 1:
					user.last_name = parts[1]
				user.save()
			login(request, user)
			return redirect('dashboard')

	else:
		form = SignupForm()
	return render(request, 'signup.html', {'form': form})


def login_view(request):
	if request.method == 'POST':
		identifier = request.POST.get('username') or request.POST.get('email')
		password = request.POST.get('password')
		# Support login by email or username
		from django.contrib.auth.models import User
		user = None
		if identifier and '@' in identifier:
			try:
				user_obj = User.objects.get(email=identifier)
				user = authenticate(request, username=user_obj.username, password=password)
			except User.DoesNotExist:
				user = None
		else:
			user = authenticate(request, username=identifier, password=password)

		if user is not None:
			login(request, user)
			return redirect('dashboard')
		else:
			return render(request, 'login.html', {'error': 'Invalid credentials'})
	return render(request, 'login.html')


def logout_view(request):
	logout(request)
	return redirect('index')


@login_required
def dashboard(request):
	orders = request.user.orders.all()
	return render(request, 'dashboard.html', {'orders': orders})


def cart_view(request):
	# minimal cart rendering (template exists)
	return render(request, 'cart.html')


def checkout_view(request):
	return render(request, 'checkout.html')
