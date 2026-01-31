import os
import django
import datetime
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FestivMartProject.settings')
django.setup()

from django.contrib.auth.models import User
from FestivMartApp.models import Category, Season, Occasion, Product

def create_initial_data():
    print("Creating superuser...")
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Superuser 'admin' created with password 'admin'")
    else:
        print("Superuser 'admin' already exists")

    print("Creating Categories...")
    
    categories_data = {
        "Fashion & Apparel": [
            "Men's Clothing", "Women's Clothing", "Kids' Wear", "Ethnic Wear", "Footwear", "Accessories (belts, caps, scarves)"
        ],
        "Electronics & Gadgets": [
            "Mobile Phones", "Laptops & Computers", "Headphones & Audio", "Smart Watches", "Cameras", "Computer Accessories"
        ],
        "Home & Living": [
            "Furniture", "Home Décor", "Kitchenware", "Storage & Organization", "Lighting", "Bedding & Bath"
        ],
        "Beauty & Personal Care": [
            "Skincare", "Haircare", "Makeup", "Fragrances", "Grooming Tools", "Organic / Herbal Products"
        ],
        "Grocery & Food": [
            "Fruits & Vegetables", "Packaged Foods", "Snacks & Beverages", "Spices & Masalas", "Sweets & Desserts", "Organic Foods"
        ],
        "Health & Wellness": [
            "Fitness Equipment", "Yoga Accessories", "Supplements", "Ayurvedic Products", "Medical Devices"
        ],
        "Sports & Outdoors": [
            "Sports Equipment", "Gym Accessories", "Outdoor Gear", "Cycling & Hiking", "Camping Products"
        ],
        "Books, Stationery & Education": [
            "Books (Academic, Fiction, Non-fiction)", "Study Materials", "Office Supplies", "Art & Craft Supplies", "School Essentials"
        ],
        "Toys, Kids & Baby": [
            "Toys & Games", "Baby Care Products", "Baby Clothing", "Educational Toys", "Kids Furniture"
        ],
        "Automotive": [
            "Bike Accessories", "Car Accessories", "Helmets", "Car Care Products", "Spare Parts"
        ],
        "Jewelry & Watches": [
            "Gold / Silver Jewelry", "Fashion Jewelry", "Smart Watches", "Traditional Jewelry"
        ],
        "Gifts & Occasions": [
            "Birthday Gifts", "Wedding Gifts", "Festival Gifts", "Personalized Items", "Greeting Cards"
        ],
        "Festival & Religious Items": [
            "Puja Items", "Diyas & Lamps", "Incense & Dhoop", "Flowers & Garlands", "Kalash & Thalis", "Kumkum & Turmeric", "Festival Decorations", "Sweets for Festivals"
        ],
        "Handicrafts & Traditional Products": [
            "Wooden Crafts", "Terracotta Items", "Brass & Copper Items", "Handloom Products", "Tribal Art"
        ],
        "Digital Products": [
            "E-books", "Online Courses", "Software Licenses", "Templates", "Subscriptions"
        ]
    }

    # Helper to get specific subcategory for product creation
    def get_subcat(parent_name, subcat_name):
        try:
            parent = Category.objects.get(name=parent_name)
            return Category.objects.get(name=subcat_name, parent=parent)
        except Category.DoesNotExist:
            # Fallback to creating a standalone category if hierarchy missing, or return None
            # Ideally this shouldn't happen if the loop below runs first
            return None

    for parent_name, subcats in categories_data.items():
        parent, _ = Category.objects.get_or_create(name=parent_name, parent=None)
        print(f"  Category: {parent_name}")
        for sub_name in subcats:
            Category.objects.get_or_create(name=sub_name, parent=parent)

    # Get categories for products (mapping to new structure where possible)
    # Using 'Fashion & Apparel' > 'Men\'s Clothing' for general clothing
    try:
        fashion_parent = Category.objects.get(name="Fashion & Apparel")
        cat_clothing = Category.objects.get(name="Men's Clothing", parent=fashion_parent)
    except Category.DoesNotExist:
        cat_clothing, _ = Category.objects.get_or_create(name="Clothing")

    try:
        electronics_parent = Category.objects.get(name="Electronics & Gadgets")
        cat_electronics = Category.objects.get(name="Smart Watches", parent=electronics_parent)
    except Category.DoesNotExist:
        cat_electronics, _ = Category.objects.get_or_create(name="Electronics")
        
    try:
        home_parent = Category.objects.get(name="Home & Living")
        cat_decor = Category.objects.get(name="Home Décor", parent=home_parent)
    except Category.DoesNotExist:
        cat_decor, _ = Category.objects.get_or_create(name="Decoration")

    print("Creating Seasons...")
    today = timezone.now().date()
    # Current active season
    season_winter, _ = Season.objects.get_or_create(
        name="Winter Sale",
        defaults={
            'start_date': today - timedelta(days=30),
            'end_date': today + timedelta(days=30),
            'description': "Best deals for the winter season!"
        }
    )
    
    # Future season
    season_summer, _ = Season.objects.get_or_create(
        name="Summer Vibes",
        defaults={
            'start_date': today + timedelta(days=120),
            'end_date': today + timedelta(days=180),
            'description': "Get ready for the heat!"
        }
    )

    print("Creating Occasions...")
    # Occasion today (or close)
    occ_special, _ = Occasion.objects.get_or_create(
        name="Special Festival",
        defaults={
            'date': today,
            'description': "A very special day!"
        }
    )

    print("Creating Products...")
    # Regular Products
    Product.objects.get_or_create(
        name="Smart Watch",
        defaults={
            'description': "A smart watch for everyone.",
            'price': 199.99,
            'category': cat_electronics,
            'available': True,
            'is_seasonal': False
        }
    )
    Product.objects.get_or_create(
        name="Classic T-Shirt",
        defaults={
            'description': "Cotton t-shirt.",
            'price': 29.99,
            'category': cat_clothing,
            'available': True,
            'is_seasonal': False
        }
    )

    # Seasonal Products
    # Linked to active season
    Product.objects.get_or_create(
        name="Winter Jacket",
        defaults={
            'description': "Keep warm in style.",
            'price': 89.99,
            'category': cat_clothing,
            'available': True,
            'is_seasonal': True,
            'season': season_winter
        }
    )
    
    Product.objects.get_or_create(
        name="Christmas Lights",
        defaults={
            'description': "Brighten up your home.",
            'price': 15.50,
            'category': cat_decor,
            'available': True,
            'is_seasonal': True,
            'season': season_winter
        }
    )
    
    # Linked to Occasion
    prod_festive, _ = Product.objects.get_or_create(
        name="Festival Special Hamper",
        defaults={
            'description': "Exclusive hamper for the special day.",
            'price': 49.99,
            'category': cat_electronics, # just an example
            'available': True,
            'is_seasonal': True
        }
    )
    prod_festive.occasions.add(occ_special)

    print("Data population complete!")

if __name__ == '__main__':
    create_initial_data()
