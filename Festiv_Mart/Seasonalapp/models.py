from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Category(models.Model):
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=120, unique=True, blank=True)

	class Meta:
		verbose_name_plural = "categories"

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)


class Product(models.Model):
	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=220, unique=True, blank=True)
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	image_url = models.URLField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)


class Order(models.Model):
	STATUS_CHOICES = [
		('created', 'Created'),
		('processing', 'Processing'),
		('completed', 'Completed'),
		('cancelled', 'Cancelled'),
	]

	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
	total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Order #{self.pk} - {self.user.username}"


class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
	quantity = models.PositiveIntegerField(default=1)
	price = models.DecimalField(max_digits=10, decimal_places=2)

	def __str__(self):
		return f"{self.quantity} x {self.product}"


class UserProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	phone = models.CharField(max_length=30, blank=True)
	address = models.TextField(blank=True)

	def __str__(self):
		return f"Profile: {self.user.username}"
