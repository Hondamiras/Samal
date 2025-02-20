from django.contrib import admin
from samal.models import Product, Category, About, Advantage, Personalization, Contact

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'price', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'updated_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_at', 'updated_at')

@admin.register(Advantage)
class AdvantageAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'image', 'created_at')

@admin.register(Personalization)
class PersonalizationAdmin(admin.ModelAdmin):
    list_display = ('title', 'image')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message', 'created_at')
    list_filter = ('created_at',)
