from django.contrib import admin
from samal.models import Product, Category, ProductImage, Service, ServiceVariant, ServiceVariantImage, WholesalePrice, ProductVariant, ProductSize, ProductColor


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    # Ваш formfield_for_foreignkey тут же остаётся
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name in ('color', 'size'):
            parent_id = request.resolver_match.kwargs.get('object_id')
            if parent_id:
                field.queryset = field.queryset.filter(product_id=parent_id)
        return field
    
    class Media:
        js = [
            'smart-selects/admin/js/chainedfk.js',
            'smart-selects/admin/js/chainedm2m.js',
            'smart-selects/admin/js/bindfields.js',
        ]
    
# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariantInline]
    list_display = ('name', 'slug', 'category', 'price', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'updated_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    class Media:
        js = [
            # вот они — пути относительно STATIC_URL
            'smart-selects/admin/js/chainedfk.js',
            'smart-selects/admin/js/chainedm2m.js',
            'smart-selects/admin/js/bindfields.js',
        ]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'id')
    list_editable = ('type',)   
    list_display_links = ('name',) 
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')

@admin.register(WholesalePrice)
class WholesalePriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'price')

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size', 'quantity')
    list_editable = ('quantity',)
    list_display_links = ('product',)  # ссылка остаётся только на продукт
    list_per_page = 10
    search_fields = ('product__name',)


    class Media:
        js = [
            'smart-selects/admin/js/chainedfk.js',
            'smart-selects/admin/js/chainedm2m.js',
            'smart-selects/admin/js/bindfields.js',
        ]
@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'size')
    list_filter = ('product', 'size')
    list_editable = ('size',)

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ('product', 'color')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}


from django.utils.html import format_html
@admin.register(ServiceVariant)
class ServiceVariantAdmin(admin.ModelAdmin):
    list_display = ('title',)
    prepopulated_fields = {'slug': ('title',)}


@admin.register(ServiceVariantImage)
class ServiceVariantImageAdmin(admin.ModelAdmin):
    list_display = ('variant', 'image')

    def image_tag(self, obj):
        return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />'.format(obj.image.url))