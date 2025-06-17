# orders/signals.py
from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import OrderItem, ProductVariant

@receiver(post_save, sender=OrderItem)
def decrease_variant_stock(sender, instance, created, **kwargs):
    """
    При создании позиции заказа списываем количество со склада,
    но только для офлайн-заказов (source='direct').
    """
    order = instance.order
    if created and order.source == "direct" and instance.product_variant:
        ProductVariant.objects.filter(pk=instance.product_variant_id).update(
            quantity=F('quantity') - instance.quantity
        )

@receiver(post_delete, sender=OrderItem)
def restore_variant_stock(sender, instance, **kwargs):
    """
    Если позиция заказа удаляется (или сам заказ откатывается),
    возвращаем товар на склад.
    """
    order = instance.order
    if order.source == "direct" and instance.product_variant:
        ProductVariant.objects.filter(pk=instance.product_variant_id).update(
            quantity=F('quantity') + instance.quantity
        )
