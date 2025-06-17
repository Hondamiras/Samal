from django.db import models
from django.utils import timezone
from samal.models import Category, Order, OrderItem, Product, ProductVariant
import uuid
from smart_selects.db_fields import ChainedForeignKey

def generate_id_name():
    # берём первые 8 символов UUID (буквы в верхнем регистре)
    return uuid.uuid4().hex[:8].upper()

class DirectOrder(models.Model):
    # инфо о клиенте
    id_name = models.CharField(
        max_length=255,
        unique=True,
        default=generate_id_name,
        verbose_name="Ид.номер",
        help_text="Автогенерируемый код для идентификации(не трогать)",
        editable=False
    )
    name = models.CharField(max_length=255, verbose_name="Имя клиента", help_text="Имя клиента")
    identification_number = models.CharField(
        max_length=255,
        verbose_name="Идентификационный номер отгрузки по М.С.",
        help_text="Введите идентификационный номер отгрузки по М.С.",
        default=generate_id_name,
        unique=True,
        editable=False
    )
    time = models.DateTimeField(default=timezone.now, verbose_name="Время заказа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta: 
        verbose_name = "открузка(офлайн-продажа)"
        verbose_name_plural = "открузки(офлайн-продажи)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}"


from django.core.exceptions import ValidationError
from django.db.models import F

class DirectOrderItem(models.Model):
    order = models.ForeignKey(
        'DirectOrder',
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Заказ"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name="Категория"
    )
    product = ChainedForeignKey(
        Product,
        chained_field="category",
        chained_model_field="category",
        show_all=False,
        auto_choose=True,
        on_delete=models.PROTECT,
        verbose_name="Наименование изделия"
    )
    product_variant = ChainedForeignKey(
        ProductVariant,
        chained_field="product",
        chained_model_field="product",
        show_all=False,
        auto_choose=True,
        on_delete=models.PROTECT,
        verbose_name="Вариант (цвет/размер)"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена за единицу"
    )

    class Meta:
        verbose_name = "Прямые продажи"
        verbose_name_plural = "Прямые продажи"

    def __str__(self):
        return f"{self.product.name} — {self.product_variant} × {self.quantity}"

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        # 1) вычисляем, сколько нужно списать
        if self.pk:
            old = DirectOrderItem.objects.get(pk=self.pk)
            delta = self.quantity - old.quantity
        else:
            delta = self.quantity

        # 2) проверяем остаток
        if self.product_variant.quantity is not None and self.product_variant.quantity < delta:
            raise ValidationError(
                f"Недостаточно товара {self.product_variant} на складе (осталось {self.product_variant.quantity})."
            )

        # 3) атомарно списываем со склада
        ProductVariant.objects.filter(pk=self.product_variant.pk).update(
            quantity=F('quantity') - delta
        )

        # 4) сохраняем саму позицию
        super().save(*args, **kwargs)    
        