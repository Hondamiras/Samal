from django.shortcuts import render
from django.db.models import Prefetch, Q
from django.core.paginator import Paginator
from .models import DirectOrder, DirectOrderItem
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required(login_url='admin:login')
def direct_orders_list(request):
    # 1) Базовый queryset с prefetch_related
    qs = DirectOrder.objects.prefetch_related(
        Prefetch(
            'items',
            queryset=DirectOrderItem.objects.select_related(
                'category', 'product', 'product_variant'
            )
        )
    )

    # 2) Фильтр по поиску и дате
    q         = request.GET.get('q', '').strip()
    date_from = request.GET.get('from')
    date_to   = request.GET.get('to')

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(id_name__iexact=q) |
            Q(identification_number__icontains=q)
        )
    if date_from:
        qs = qs.filter(time__date__gte=date_from)
    if date_to:
        qs = qs.filter(time__date__lte=date_to)

    # 3) Пагинация
    paginator = Paginator(qs, 10)          # 10 заказов на страницу
    page_num  = request.GET.get('page', 1)
    page_obj  = paginator.get_page(page_num)

    # 4) Группировка и подсчёт итогов только для заказов на этой странице
    for order in page_obj:
        grouped = {}
        for item in order.items.all():
            vid = item.product_variant_id
            if vid not in grouped:
                grouped[vid] = {
                    'category':    item.category.name,
                    'product':     item.product.name,
                    'variant':     str(item.product_variant),
                    'quantity':    0,
                    'unit_price':  0.0,
                    'total_price': 0.0,
                }
            grp = grouped[vid]
            grp['quantity']    += item.quantity
            grp['unit_price']  += float(item.unit_price)
            grp['total_price'] += float(item.total_price)

        order.grouped_items    = list(grouped.values())
        order.total_quantity   = sum(g['quantity']    for g in order.grouped_items)
        order.total_price      = sum(g['total_price'] for g in order.grouped_items)

    # 5) Рендерим
    return render(request, 'direct_sales/direct_orders.html', {
        'page_obj':   page_obj,
        'q':          q,
        'date_from':  date_from,
        'date_to':    date_to,
    })
