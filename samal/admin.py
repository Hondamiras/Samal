from django.contrib import admin
from samal.models import Product, Category, ProductImage, WholesalePrice, ProductVariant, ProductSize, ProductColor

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'price', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'updated_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')

@admin.register(WholesalePrice)
class WholesalePriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'price')

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size')

@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'size')

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ('product', 'color')

