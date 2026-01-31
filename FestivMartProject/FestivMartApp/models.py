from django.db import models
from django.utils import timezone
from decimal import Decimal

class Season(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField(help_text="Start date for the current year")
    end_date = models.DateField(help_text="End date for the current year")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Occasion(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField(help_text="Date of the occasion for the current year")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="Alternative to uploading: provide an image URL")
    
    # Stock and Pricing
    stock = models.PositiveIntegerField(default=1)
    discount_percent = models.PositiveIntegerField(default=0, help_text="Discount percentage (0-100)")
    
    # Seasonal Logic
    is_seasonal = models.BooleanField(default=False)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    occasions = models.ManyToManyField(Occasion, blank=True, related_name='products')
    
    available = models.BooleanField(default=True)
    seller = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    @property
    def discounted_price(self):
        """Returns the price after applying discount"""
        if self.discount_percent > 0:
            return self.price * (Decimal('100') - Decimal(self.discount_percent)) / Decimal('100')
        return self.price
    
    @property
    def is_in_stock(self):
        """Returns True if product is in stock"""
        return self.stock > 0
    
    def get_image_url(self):
        """Returns the image URL - either from uploaded file or from URL field"""
        if self.image:
            return self.image.url
        elif self.image_url:
            return self.image_url
        else:
            return 'https://via.placeholder.com/400x400?text=No+Image'


class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    is_business = models.BooleanField(default=False)
    business_name = models.CharField(max_length=200, blank=True)
    badges = models.JSONField(default=list, blank=True)
    level = models.IntegerField(default=1)
    total_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {'Business' if self.is_business else 'Customer'}"


class Cart(models.Model):
    """Shopping cart for users"""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=100, null=True, blank=True)  # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    discount_percent = models.PositiveIntegerField(default=0)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart ({self.session_key})"
    
    @property
    def subtotal(self):
        """Calculate subtotal before discounts"""
        total = sum(item.line_total for item in self.items.all())
        return total if total else Decimal('0')
    
    @property
    def discount_amount(self):
        """Calculate discount amount"""
        if self.discount_percent > 0:
            return self.subtotal * Decimal(self.discount_percent) / Decimal('100')
        return Decimal('0')
    
    @property
    def tax_amount(self):
        """Calculate 10% GST"""
        return (self.subtotal - self.discount_amount) * Decimal('0.10')
    
    @property
    def shipping_cost(self):
        """Free shipping over ₹1000"""
        subtotal = self.subtotal
        if subtotal >= Decimal('1000') or subtotal == Decimal('0'):
            return Decimal('0')
        return Decimal('99')  # Flat shipping rate
    
    @property
    def total(self):
        """Calculate final total"""
        return self.subtotal - self.discount_amount + self.tax_amount + self.shipping_cost
    
    @property
    def item_count(self):
        """Total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    def apply_coupon(self, code):
        """Apply a coupon code"""
        valid_coupons = {
            'FESTIV20': 20,
            'SAVE10': 10,
            'HOLI15': 15,
            'DIWALI25': 25,
        }
        code = code.upper()
        if code in valid_coupons:
            self.coupon_code = code
            self.discount_percent = valid_coupons[code]
            self.save()
            return True, f"Coupon applied! You got {valid_coupons[code]}% off."
        return False, "Invalid coupon code."
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
        self.coupon_code = None
        self.discount_percent = 0
        self.save()


class CartItem(models.Model):
    """Individual item in a cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    @property
    def unit_price(self):
        """Get the effective price (with discount if applicable)"""
        return self.product.discounted_price
    
    @property
    def line_total(self):
        """Calculate line total"""
        return self.unit_price * self.quantity


class Order(models.Model):
    """Completed orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Address
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Order totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    
    # Payment
    payment_method = models.CharField(max_length=50, default='cod')  # cod, card, upi
    payment_status = models.CharField(max_length=20, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import random
            import string
            self.order_number = 'FM' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)  # Store name in case product is deleted
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
