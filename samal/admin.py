from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from samal.models import Product, Category, ProductImage, Service, ServiceVariant, ServiceVariantImage, WholesalePrice, ProductVariant, ProductSize, ProductColor


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ('color', 'size', 'quantity')
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
    list_display = ('name', 'category', 'price')
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
    list_filter = ('product',)

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
    change_form_template = 'admin/samal/productvariant/change_form.html'

    # 1) Добавляем свой URL для AJAX
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'matrix/<int:product_id>/',
                self.admin_site.admin_view(self.matrix_view),
                name='samal_productvariant_matrix'
            ),
        ]
        return custom + urls

    # 2) Представление, отдающее JSON с матрицей
    def matrix_view(self, request, product_id):
        # Получаем модель продукта из ForeignKey
        prod_model = ProductVariant._meta.get_field('product').related_model
        product = prod_model.objects.filter(pk=product_id).first()
        if not product:
            return JsonResponse({'error': 'no product'}, status=404)

        # Собираем все варианты, цвета, размеры
        variants = list(product.variants.select_related('color', 'size'))
        colors   = sorted({v.color for v in variants}, key=lambda c: str(c))
        sizes    = sorted({v.size  for v in variants}, key=lambda s: str(s))

        # Строим строки с подсчётом row_total
        rows = []
        for color in colors:
            quantities = []
            for size in sizes:
                v = next((x for x in variants if x.color==color and x.size==size), None)
                quantities.append(v.quantity if v else 0)
            row_total = sum(quantities)
            rows.append({
                'color':      str(color),
                'quantities': quantities,
                'row_total':  row_total,
            })

        # Суммы по столбцам и общий итог
        totals      = [sum(row['quantities'][i] for row in rows) for i in range(len(sizes))]
        grand_total = sum(totals)

        return JsonResponse({
            'sizes':       [str(s) for s in sizes],
            'rows':        rows,
            'totals':      totals,
            'grand_total': grand_total,
        })

    # 3) changeform_view передаёт минимальный контекст (остальная отрисовка идёт через AJAX)
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        # Нам не нужны сразу product_colors и пр. — всё подтянется через AJAX
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context) 
    class Media:
        js = [
            'smart-selects/admin/js/chainedfk.js',
            'smart-selects/admin/js/chainedm2m.js',
            'smart-selects/admin/js/bindfields.js',
            'admin/js/productvariant_matrix.js',
        ]


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'size')
    list_filter = ('product', 'size')
    search_fields = ('size',)
    list_per_page = 10

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ('product', 'color')
    search_fields = ('color',)
    list_filter = ('product',) 
    list_per_page = 10

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