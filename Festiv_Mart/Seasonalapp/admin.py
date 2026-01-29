from django.contrib import admin
from .models import Category, Product, Order, OrderItem, UserProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ("name", "category", "price", "is_active", "created_at")
	list_filter = ("is_active", "category")
	search_fields = ("name", "description")
	prepopulated_fields = {"slug": ("name",)}


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "status", "total", "created_at")
	list_filter = ("status", "created_at")
	inlines = (OrderItemInline,)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "phone")
