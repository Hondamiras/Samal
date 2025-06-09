# samal/management/commands/expire_orders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from samal.models import Order

class Command(BaseCommand):
    help = "Отменяет все неоплаченные (status='new') заказы старше 24 часов без изменения складских остатков"

    def handle(self, *args, **options):
        now = timezone.now()
        threshold = now - timezone.timedelta(hours=24)
        expired_qs = Order.objects.filter(status='new', created_at__lte=threshold)
        count = expired_qs.count()
        expired_qs.update(status='canceled')
        self.stdout.write(self.style.SUCCESS(f"Отменено {count} просроченных заказов."))
