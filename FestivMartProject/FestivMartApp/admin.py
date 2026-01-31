from django.contrib import admin
from .models import Category, Season, Occasion, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ['name']

@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')
    list_filter = ('date',)
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_seasonal', 'available')
    list_filter = ('available', 'is_seasonal', 'category', 'season', 'occasions')
    search_fields = ('name', 'description')
    autocomplete_fields = ['season', 'occasions']
