from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from smart_selects.widgets import ChainedSelect

from direct_sales.models import DirectOrder, DirectOrderItem
from samal.models import ProductVariant, Product

# ——— 0) Кастомные заголовки админки
admin.site.site_header = "Samal Admin"
admin.site.site_title = "Samal Admin Панель"
admin.site.index_title = "Добро пожаловать в панель управления Samal"

# ——— 1) Форма для DirectOrderItem: динамический queryset, min/max, help + валидация
class DirectOrderItemForm(forms.ModelForm):
    class Meta:
        model = DirectOrderItem
        fields = ('category', 'product', 'product_variant', 'quantity', 'unit_price')
        linked_fields = ('product', 'product_variant')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Определяем продукт для фильтрации вариантов
        product_selected = None
        # если заполнено в POST
        prod_name = self.add_prefix('product')
        if prod_name in self.data:
            try:
                product_selected = Product.objects.get(pk=self.data.get(prod_name))
            except Exception:
                product_selected = None
        # если редактируем существующий item
        elif self.instance.pk:
            product_selected = self.instance.product

        # Устанавливаем queryset для product_variant
        if product_selected:
            self.fields['product_variant'].queryset = ProductVariant.objects.filter(product=product_selected)
        else:
            self.fields['product_variant'].queryset = ProductVariant.objects.none()

        # Конфигурируем min/max и help для quantity
        pv = getattr(self.instance, 'product_variant', None)
        stock = pv.quantity if pv else 0
        fld = self.fields['quantity']
        fld.widget.attrs.update({'min': 1, 'max': stock})
        fld.help_text = f"Макс. на складе: {stock} шт."

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        pv = self.cleaned_data.get('product_variant')
        if qty < 1:
            raise forms.ValidationError("Количество должно быть не меньше 1")
        if pv and qty > (pv.quantity or 0):
            raise forms.ValidationError(f"Нельзя взять больше, чем есть на складе ({pv.quantity})")
        return qty

# ——— 2) Расширяем ChainedSelect, чтобы дописать data-stock
class StockChainedSelect(ChainedSelect):
    def create_option(self, name, value, label, selected, index,
                      subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index,
            subindex=subindex, attrs=attrs
        )
        # Пропускаем пустой вариант
        if value:
            try:
                pv = ProductVariant.objects.get(pk=value)
                option['attrs']['data-stock'] = pv.quantity
            except ProductVariant.DoesNotExist:
                option['attrs']['data-stock'] = 0
        return option

# ——— 3) Inline: заменяем widget product_variant на StockChainedSelect
class DirectOrderItemInline(admin.TabularInline):
    model = DirectOrderItem
    form = DirectOrderItemForm
    extra = 1

    readonly_fields = ('available_stock',)
    fields = (
        'category', 'product', 'product_variant',
        'quantity', 'available_stock', 'unit_price',
    )

    def available_stock(self, obj):
        return obj.product_variant.quantity if obj and obj.product_variant else '-'
    available_stock.short_description = 'В наличии'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'product_variant' and formfield:
            widget = formfield.widget
            if isinstance(widget, RelatedFieldWidgetWrapper):
                inner = widget.widget
                if isinstance(inner, ChainedSelect):
                    inner.__class__ = StockChainedSelect
            elif isinstance(widget, ChainedSelect):
                widget.__class__ = StockChainedSelect
        return formfield

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'smart_selects/admin/js/chainedfk.js',
            'direct_sales/js/inline_stock.js',
        )

# ——— 4) Регистрация DirectOrder вместе с inline
@admin.register(DirectOrder)
class DirectOrderAdmin(admin.ModelAdmin):
    list_display = ('id_name', 'name', 'identification_number', 'time', 'created_at')
    readonly_fields = ('id_name', 'created_at')
    search_fields = ('id_name', 'name', 'identification_number')
    list_filter = ('created_at', 'time')
    ordering = ('-created_at',)
    inlines = [DirectOrderItemInline]

# ——— 5) Standalone-админ для DirectOrderItem (если нужен)
@admin.register(DirectOrderItem)
class DirectOrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order', 'category', 'product',
        'product_variant', 'quantity', 'unit_price', 'available_stock'
    )
    search_fields = ('order__id_name', 'product__name', 'order__name')
    list_filter = ('category', 'product')

    def available_stock(self, obj):
        return obj.product_variant.quantity if obj and obj.product_variant else '-'
    available_stock.short_description = 'В наличии'