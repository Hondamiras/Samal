from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_list_or_404, redirect, render, get_object_or_404
from samal.models import (
    Cart, CartItem, Like, Product, Category,
    ProductColor, ProductImage, ProductSize, ProductVariant, Service, ServiceVariant, WholesalePrice
)
from samal.forms import ContactForm
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

# =====================================================
# Вспомогательные функции
# =====================================================

def get_session_key(request):
    """
    Получаем идентификатор сессии, если его нет — создаём новую сессию.
    """
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    return session_key

def get_unit_price(item):
    """
    Возвращает оптовую цену, если количество товара в корзине
    соответствует или превышает заданный порог,
    иначе возвращает обычную цену продукта.
    """
    if item.product_variant:
        product = item.product_variant.product
    else:
        product = None

    if product:
        # Ищем оптовую цену, где требуемое количество <= количеству товара
        wholesale_price = product.wholesale_prices.filter(quantity__lte=item.quantity).order_by('-quantity').first()
        if wholesale_price:
            return wholesale_price.price
        return product.price
    return 0

def item_total(item):
    """
    Вычисляет общую стоимость товара в корзине (цена за единицу * количество).
    """
    return get_unit_price(item) * item.quantity

def calculate_cart_total(session_key):
    """
    Вычисляет общую стоимость корзины для текущей сессии.
    """
    cart_items = CartItem.objects.filter(cart__session_key=session_key)
    total = sum(get_unit_price(item) * item.quantity for item in cart_items)
    return total

# =====================================================
# Основные страницы и представления
# =====================================================
def category(request):
    # Получаем все категории
    categories = Category.objects.all().order_by('id')

    # Если фильтр по типу передан, отфильтруем категории (либо товары)
    product_type = request.GET.get('type')
    if product_type:
        # Фильтруем категории по типу продукта
        categories = categories.filter(type=product_type)
    
    # Если также нужны товары для вывода, можно добавить запрос:
    # products = Product.objects.filter(category__in=categories)
    context = {
        'categories': categories,
        # 'products': products, если требуется вывод товаров
        'sort_option': request.GET.get('sort'),
    }
    return render(request, 'samal/category.html', context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products_list = Product.objects.filter(category=category).order_by('id')
    sort_option = request.GET.get('sort', '')
    
    # Получаем параметры фильтрации из GET-запроса
    color = request.GET.get('color')           # например, "red"
    size = request.GET.get('size')             # например, "M"
    min_price = request.GET.get('min_price')   # например, "1000"
    max_price = request.GET.get('max_price')   # например, "5000"
    gender = request.GET.get('gender')         # например, "female", "male", "kids", "unisex"
    avail = request.GET.get('availability')    # 'in_stock' или 'on_order'

    # Фильтрация по цене
    if min_price:
        try:
            products_list = products_list.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products_list = products_list.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Фильтрация по наличию
    if avail in ['in_stock', 'on_order']:
        products_list = products_list.filter(availability=avail)
    
    # Фильтрация по цвету через связанную модель ProductColor
    if color:
        products_list = products_list.filter(colors__color__icontains=color)
    # Фильтрация по размеру через связанную модель ProductSize
    if size:
        products_list = products_list.filter(sizes__size__icontains=size)
    if gender:
        products_list = products_list.filter(gender__iexact=gender)

    # Сортировка
    if sort_option == 'price_asc':
        products_list = products_list.order_by('price')
    elif sort_option == 'price_desc':
        products_list = products_list.order_by('-price')
    elif sort_option == 'newest':
        products_list = products_list.order_by('-created_at')

    paginator = Paginator(products_list, 6)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'category': category,
        'products': products,
        'sort_option': sort_option,
        # Передаём фильтры в контекст для сохранения выбранных значений в форме
        'filters': {
            'color': color or '',
            'size': size or '',
            'min_price': min_price or '',
            'max_price': max_price or '',
            'gender': gender or '',
            'availability': avail or '',
        },
    }
    return render(request, 'samal/category_detail.html', context)

def product_search(request):
    query = request.GET.get('q', '').strip()
    products_list = Product.objects.all()

    if query:
        products_list = products_list.filter(
            Q(name__icontains=query) | Q(id__icontains=query)
        ).distinct()

    paginator = Paginator(products_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj.object_list,
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'samal/search_results.html', context)


import json
from django.shortcuts import get_object_or_404, render
from .models import OrderItem, Product, Category, ProductColor, ProductSize, Like

# Порядок колонок-­размеров
SIZE_ORDER = ['5XS', '4XS', '3XS', '2XS', 'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL', '6XL', '7XL', '8XL', '9XL', '10XL']

def product_detail(request, slug):
    # 0) Базовые объекты
    product = get_object_or_404(Product, slug=slug)
    category = get_object_or_404(Category, slug=product.category.slug)
    product_images   = product.product_images.all()
    wholesale_prices = product.wholesale_prices.all()

    # 1) Все варианты (цвет+размер+количество)
    variants = product.variants.select_related('color', 'size').all()

    # 2) Оригинальные списки цветов/размеров (если они где-то ещё используются)
    if variants.exists():
        product_colors = ProductColor.objects.filter(
            product=product,
            id__in=variants.values_list('color', flat=True)
        ).distinct()
        product_sizes = ProductSize.objects.filter(
            product=product,
            id__in=variants.values_list('size', flat=True)
        ).distinct()
    else:
        product_colors = ProductColor.objects.none()
        product_sizes  = ProductSize.objects.none()

    # 3) На всякий случай — JSON для вашего JS, как было раньше
    grouped = {}
    for v in variants:
        cmap = grouped.setdefault(v.color.id, [])
        cmap.append({
            'size_id':   v.size.id,
            'size_name': v.size.size,
            'quantity':  v.quantity,
        })
    variants_json = json.dumps(grouped, ensure_ascii=False)

    # 4) Динамика таблицы
    # 4.1) Какие размеры реально есть?
    all_size_names = {v.size.size for v in variants}

    # 1) основные размеры в том порядке, который вы сами задали:
    base = [sz for sz in SIZE_ORDER if sz in all_size_names]

    # 2) а вот все XL-соффиксы, которых нет в SIZE_ORDER,
    #    в порядке возрастания числа перед «XL»
    extras = sorted(
        [sz for sz in all_size_names if sz not in base and sz.endswith('XL')],
        key=lambda s: int(s.rstrip('XL') or 1)
    )

    # 3) финальный список колонок:
    size_headers = base + extras


    # 4.2) Построим map: color_id → { size_name: quantity }
    color_size_map = {}
    for v in variants:
        cmap = color_size_map.setdefault(v.color.id, {})
        cmap[v.size.size] = v.quantity

    # 4.3) Собираем строки для таблицы
    rows = []
    for color in product_colors:
        cmap = color_size_map.get(color.id, {})
        quantities = [ cmap.get(sz, 0) for sz in size_headers ]
        rows.append({
            'color':     color,
            'quantities': quantities,
            'row_total': sum(quantities),
        })

    # 4.4) Считаем итоги по каждому размеру и общий итог
    totals      = [ sum(row['quantities'][i] for row in rows) for i in range(len(size_headers)) ]
    grand_total = sum(totals)

    # 5) Смотрим, лайкал ли уже пользователь
    session_key = get_session_key(request)
    liked       = Like.objects.filter(product=product, session_key=session_key).exists()

    # 6) Рендерим всё в контекст
    return render(request, 'samal/product_detail.html', {
        'product':         product,
        'category':        category,
        'product_images':  product_images,
        'wholesale_prices': wholesale_prices,

        # для старой логики
        'product_colors': product_colors,
        'product_sizes':  product_sizes,
        'variants_json':  variants_json,
        'liked':          liked,

        # для динамической таблички
        'size_headers':   size_headers,
        'rows':           rows,
        'totals':         totals,
        'grand_total':    grand_total,
    })


from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
import logging
from django.core.mail import EmailMessage
import requests


logger = logging.getLogger(__name__)

@csrf_protect
def contact_view(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            # 1) собираем данные из формы
            name    = form.cleaned_data['name']
            phone   = form.cleaned_data['phone']
            email   = form.cleaned_data['email']
            message = form.cleaned_data['message']

            subject = f'Новое сообщение от {name}'
            body = (
                f"Имя: {name}\n"
                f"Телефон: {phone}\n"
                f"Email: {email}\n\n"
                f"{message}"
            )

            # 2) формируем и отправляем письмо
            email_msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,   # no-reply@samaltrading.kz
                to=[settings.CONTACT_EMAIL],              # ваш gmail
                reply_to=[email],                         # чтобы вы могли ответить пользователю
            )
            try:
                sent = email_msg.send(fail_silently=False)
                logger.info("EmailMessage.send() returned %d", sent)
            except Exception as exc:
                logger.error("Ошибка отправки письма: %s", exc, exc_info=True)
                messages.error(request, 'Не удалось отправить сообщение. Попробуйте позже.')
            else:
                messages.success(request, 'Ваше сообщение успешно отправлено!')
                return redirect('contact')

        else:
            # сюда попадут и ошибки полей, и ошибки капчи
            messages.error(request, 'Пожалуйста, заполните все поля и подтвердите, что вы не робот.')

    return render(request, 'samal/contact.html', {'form': form})
    
# =====================================================
# Функции для работы с лайками
# =====================================================

def toggle_like(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    session_key = get_session_key(request)
    like, created = Like.objects.get_or_create(session_key=session_key, product=product)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'success': True, 'liked': liked})

def liked_products(request):
    session_key = request.session.session_key
    likes = Like.objects.filter(session_key=session_key) if session_key else []
    return render(request, 'samal/liked_products.html', {'likes': likes})

def remove_favorite(request, slug):
    if request.method == "POST":
        # Предполагаем, что у вас есть логика, связанная с session_key или пользователем
        like = get_object_or_404(Like, product__slug=slug)
        like.delete()
        return JsonResponse({'success': True, 'message': 'Товар удален из избранного'})
    return JsonResponse({'success': False, 'message': 'Метод POST обязателен'}, status=405)

# =====================================================
# Функции для работы с корзиной
# =====================================================

def add_to_cart(request, product_slug):
    """
    Добавляет товар в корзину.
    Если в POST-запросе присутствуют ключи вида "variants-<i>-quantity",
    обрабатывается множественный вариант, иначе — одиночный вариант.
    Для варианта обязательно должны быть указаны color_id и size_id.
    """
    product = get_object_or_404(Product, slug=product_slug)
    session_key = get_session_key(request)
    cart, _ = Cart.objects.get_or_create(session_key=session_key)

    # Обработка множественных вариантов
    variants = []
    i = 0
    while f'variants-{i}-quantity' in request.POST:
        try:
            quantity = int(request.POST.get(f'variants-{i}-quantity', 1))
        except ValueError:
            quantity = 1

        color_id = request.POST.get(f'variants-{i}-color_id')
        size_id = request.POST.get(f'variants-{i}-size_id')

        # Если оба параметра указаны, ищем вариант
        if color_id and size_id:
            variant = get_object_or_404(ProductVariant, product=product, color_id=color_id, size_id=size_id)
            variants.append({
                'quantity': quantity,
                'variant': variant,
            })
        i += 1

    if variants:
        for variant_data in variants:
            variant = variant_data['variant']
            quantity_to_add = variant_data['quantity']
            # Проверяем, есть ли уже данный вариант в корзине
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_variant=variant,
                defaults={'quantity': 0}
            )
            new_quantity = cart_item.quantity + quantity_to_add

            # Если итоговое количество превышает доступное, возвращаем ошибку
            if new_quantity > variant.quantity:
                available_to_add = variant.quantity - cart_item.quantity
                return JsonResponse({
                    'success': False,
                    'message': (
                        f"Невозможно добавить {quantity_to_add} шт. для варианта "
                        f"{variant.product.name} (цвет: {variant.color}, размер: {variant.size}). "
                        f"Доступно для добавления: {available_to_add if available_to_add > 0 else 0}."
                    )
                }, status=400)

            # Обновляем количество
            cart_item.quantity = new_quantity
            cart_item.save()

        return JsonResponse({
            'success': True,
            'message': 'Варианты успешно добавлены в корзину'
        })

    # Если множественных вариантов нет, обрабатываем одиночный вариант
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1

    color_id = request.POST.get('color_id')
    size_id = request.POST.get('size_id')
    if not (color_id and size_id):
        return JsonResponse({'success': False, 'message': 'Выберите цвет и размер'}, status=400)

    variant = get_object_or_404(ProductVariant, product=product, color_id=color_id, size_id=size_id)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product_variant=variant,
        defaults={'quantity': 0}
    )
    new_quantity = cart_item.quantity + quantity

    if new_quantity > variant.quantity:
        available_to_add = variant.quantity - cart_item.quantity
        return JsonResponse({
            'success': False,
            'message': (
                f"Невозможно добавить {quantity} шт. для варианта "
                f"{variant.product.name} (цвет: {variant.color}, размер: {variant.size}). "
                f"Доступно для добавления: {available_to_add if available_to_add > 0 else 0}."
            )
        }, status=400)

    cart_item.quantity = new_quantity
    cart_item.save()

    return JsonResponse({
        'success': True,
        'message': 'Товар успешно добавлен в корзину',
        'quantity': cart_item.quantity,
    })


def cart_detail(request):
    session_key = get_session_key(request)
    cart = Cart.objects.filter(session_key=session_key).first()
    cart_items = cart.items.select_related('product_variant__color', 'product_variant__size').all() if cart else []
    
    # Calculate total price from items
    total_price = sum(item.total_price for item in cart_items)

    # If the cart isn't empty, we can retrieve the product from the first CartItem
    product = None
    if cart_items:
        first_variant = cart_items[0].product_variant
        if first_variant and getattr(first_variant, 'product', None) and first_variant.product.slug:
            product = first_variant.product
    
    # If cart is empty or no product was found, just pick the first product in DB (optional fallback)
    if not product:
        product = Product.objects.first()

    return render(request, 'samal/cart_detail.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'product': product,
    })

def update_cart_quantity(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        session_key = get_session_key(request)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__session_key=session_key)
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Корзина не найдена'}, status=404)

        if action == 'plus':
            cart_item.quantity += 1
        elif action == 'minus':
            cart_item.quantity -= 1
        elif action == 'set':
            try:
                new_quantity = int(request.POST.get('quantity', 0))
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Неверное значение количества'}, status=400)
            cart_item.quantity = new_quantity

        if cart_item.quantity <= 0:
            # quantity fell to 0 or below, remove item entirely
            cart_item.delete()
            new_quantity = 0
            item_total = 0
            cart_total = calculate_cart_total(session_key)
            is_wholesale = False
            unit_display = ""
            price_to_use = 0
            wholesale = None
        else:
            cart_item.save()
            new_quantity = cart_item.quantity
            
            # Get the "regular" or "wholesale" price, depending on quantity
            price_to_use = get_unit_price(cart_item)
            item_total = price_to_use * new_quantity
            
            # Recalculate entire cart
            cart_total = calculate_cart_total(cart_item.cart.session_key)
            
            # Check if user qualifies for a wholesale price
            wholesale = cart_item.product_variant.product.wholesale_prices.filter(
                quantity__lte=new_quantity
            ).order_by('-quantity').first()
            is_wholesale = bool(wholesale)
            
            # e.g. kg, pcs, etc.
            unit_display = cart_item.product_variant.product.get_unit_display()

        return JsonResponse({
            'success': True,
            'quantity': new_quantity,
            'item_total': item_total,
            'cart_total': cart_total,
            'is_wholesale': is_wholesale,
            'unit_price': price_to_use,
            'wholesale_price': wholesale.price if wholesale and new_quantity > 0 else None,
            'regular_price': cart_item.product_variant.product.price if new_quantity > 0 else None,
            'unit_display': unit_display,
            'new_price': price_to_use
        })
    else:
        return JsonResponse({'success': False, 'error': 'Метод POST обязателен'}, status=405)

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('cart_detail')


def remove_cart_item_ajax(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        session_key = get_session_key(request)
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__session_key=session_key)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'CartItem not found'}, status=404)
        cart = Cart.objects.filter(session_key=session_key).first()
        cart_total = sum(get_unit_price(ci) * ci.quantity for ci in cart.items.all()) if cart else 0
        return JsonResponse({
            'success': True,
            'cart_total': cart_total
        })
    else:
        return JsonResponse({'success': False, 'error': 'Метод POST обязателен'}, status=405)


def clear_cart(request):
    if request.method == 'POST':
        session_key = get_session_key(request)
        Cart.objects.filter(session_key=session_key).delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Метод POST обязателен'}, status=405)


# =====================================================
# Функции для оформления заказа
# =====================================================
from django.db import transaction
from django.db.models import F
from django.utils import timezone

# -------------  ОФОРМЛЕНИЕ ЗАКАЗА  -----------------

def order_view(request):
    session_key = get_session_key(request)
    cart = Cart.objects.filter(session_key=session_key).first()

    # Подтягиваем связанные данные через product_variant
    if cart:
        cart_items = cart.items.select_related(
            'product_variant__product',
            'product_variant__color',
            'product_variant__size'
        ).all()
    else:
        cart_items = []

    total_price = sum(item.total_price for item in cart_items)

    initial_ctx = {
        'cart_items':  cart_items,
        'total_price': total_price,
        'name':  '', 'email': '', 'phone': '', 'address': '', 'comment': '',
    }

    if not cart_items:
        messages.error(request, 'Корзина пуста')
        return render(request, 'samal/order.html', initial_ctx)

    if request.method == 'POST':
        # Проверка минималки
        if total_price < 75000:
            messages.error(request, 'Минимальная сумма заказа — 75000 ₸')
            return render(request, 'samal/order.html', initial_ctx)

        # Считываем поля формы
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        comment = request.POST.get('comment', '').strip()

        if not name or not phone:
            messages.error(request, 'Имя и телефон обязательны')
            initial_ctx.update({
                'name': name, 'email': email, 'phone': phone,
                'address': address, 'comment': comment,
            })
            return render(request, 'samal/order.html', initial_ctx)

        # Проверяем остатки на складе перед резервом
        for item in cart_items:
            variant = item.product_variant
            if not variant:
                messages.error(request, 'В корзине есть некорректный товар.')
                return render(request, 'samal/order.html', initial_ctx)

            if variant.quantity < item.quantity:
                messages.error(
                    request,
                    f"Недостаточно на складе «{variant.product.name}» "
                    f"{variant.color.color}/{variant.size.size}"
                )
                return render(request, 'samal/order.html', initial_ctx)

        try:
            with transaction.atomic():
                # 1) Создаём Order
                order = Order.objects.create(
                    name=name,
                    email=email or '',
                    phone=phone,
                    address=address or '',
                    comment=comment or '',
                    total_price=Decimal(total_price),
                    status='new',
                    # created_at проставится автоматически AutoNowAdd
                )

                order_cart_items = []

                # 2) Создаём OrderItem и резервируем запасы
                for item in cart_items:
                    variant = item.product_variant
                    product = variant.product

                    unit_price = get_unit_price(item)
                    total_item = item_total(item)

                    OrderItem.objects.create(
                        order=order,
                        product_variant=variant,
                        product_name=product.name,
                        quantity=item.quantity,
                        unit_price=unit_price,
                        total_price=Decimal(total_item),
                    )

                    # резервируем
                    variant.quantity = F('quantity') - item.quantity
                    variant.save(update_fields=['quantity'])

                    order_cart_items.append({
                        'product_name': product.name,
                        'color':         variant.color.color,
                        'size':          variant.size.size,
                        'quantity':      item.quantity,
                        'unit_price':    str(unit_price),
                        'total_price':   str(total_item),
                    })

                # 3) Отправка письма
                subject = f'Новый заказ от {name}'
                lines = ['Детали заказа:', '-'*40]
                for idx, oi in enumerate(order_cart_items, start=1):
                    lines += [
                        f"{idx}. {oi['product_name']} — {oi['color']}/{oi['size']}",
                        f"   Кол-во: {oi['quantity']}  ×  {oi['unit_price']} ₸  =  {oi['total_price']} ₸",
                        '-'*40
                    ]
                lines += [
                    f'Общая сумма: {total_price} ₸',
                    '',
                    'Контакты:',
                    f'Имя: {name}',
                    f'Email: {email or "—"}',
                    f'Телефон: {phone}',
                    f'Адрес: {address or "—"}',
                    f'Комментарий: {comment or "—"}',
                ]
                send_mail(
                    subject=subject,
                    message='\n'.join(lines),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ORDER_EMAIL] + ([email] if email else []),
                )

                # 4) Очищаем корзину и сохраняем в сессии
                cart.delete()
                request.session['last_order_id'] = order.id
                request.session['order_data'] = {
                    'order_id':       order.id,
                    'creation_date':  order.created_at.strftime('%d.%m.%Y %H:%M'),
                    'cart_items':     order_cart_items,
                    'total_price':    str(total_price),
                    'name':           name,
                    'email':          email,
                    'phone':          phone,
                    'address':        address,
                    'comment':        comment,
                }

        except Exception:
            messages.error(request, 'Произошла ошибка при сохранении заказа. Попробуйте ещё раз.')
            return render(request, 'samal/order.html', initial_ctx)

        messages.success(request, 'Ваш заказ успешно принят! Пожалуйста, оплатите его в течение 24 часов.')
        return redirect('order_success')

    # GET
    return render(request, 'samal/order.html', initial_ctx)
# =====================================================
# Страница успешного оформления заказа
# =====================================================
def order_success_view(request):
    order_id = request.session.get("last_order_id")
    order = None
    cart_items = []
    total_price = 0
    name = phone = email = address = comment = ""

    if order_id:
        order = Order.objects.filter(id=order_id).first()
        if order:
            # извлекаем детали из order
            name        = order.name
            phone       = order.phone
            email       = order.email
            address     = order.address
            comment     = order.comment
            total_price = order.total_price
            # получаем список позиций (OrderItem) переданного заказа
            cart_items = order.items.all()

            # Если вы хотите, чтобы данные сохранялись после перезагрузки,
            # НЕ УДАЛЯЙТЕ эту строку:
            # del request.session['last_order_id']

    return render(request, "samal/order_success.html", {
        "order": order,
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "comment": comment,
        "cart_items": cart_items,
        "total_price": total_price,
    })

# =====================================================
# Админка для менеджеров
# =====================================================
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from .models import Order
from django.db.models import Sum


@staff_member_required(login_url='admin:login')
def orders_list_view(request):
    # 1) Отмечаем и обрабатываем просроченные заказы (статус 'new' старше 24 ч.)
    now = timezone.now()
    threshold = now - timezone.timedelta(hours=24)
    expired_orders = Order.objects.filter(status='new', created_at__lte=threshold)
    for order in expired_orders:
        order.status = 'canceled'
        order.save(update_fields=['status'])
        # восстанавливаем запасы
        for item in order.items.all():
            variant = item.product_variant
            if variant:
                variant.quantity = F('quantity') + item.quantity
                variant.save(update_fields=['quantity'])
            else:
                prod = Product.objects.filter(name=item.product_name).first()
                if prod:
                    prod.quantity = F('quantity') + item.quantity
                    prod.save(update_fields=['quantity'])

    # 2) Фильтрация по статусу из GET-параметра
    requested_status = request.GET.get('status', '')
    valid_statuses = {key for key, _ in Order.STATUS_CHOICES}
    if requested_status in valid_statuses:
        orders = Order.objects.filter(status=requested_status).order_by('-created_at')
    else:
        orders = Order.objects.all().order_by('-created_at')
        requested_status = ''

    # 3) Подсчёт общей суммы и количества
    aggregate_data = orders.aggregate(total_sum=Sum('total_price'))
    total_sum = aggregate_data['total_sum'] or Decimal('0')
    orders_count = orders.count()

    context = {
        'orders': orders,
        'requested_status': requested_status,
        'all_statuses': Order.STATUS_CHOICES,
        'orders_total_sum': total_sum,
        'orders_total_count': orders_count,
    }
    return render(request, 'samal/orders_list.html', context)

@staff_member_required(login_url='admin:login')
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # рассчитываем дедлайн оплаты
    payment_deadline = order.created_at + timezone.timedelta(hours=24)

    # 1) Авто-отмена, если просрочен
    if order.status == 'new' and timezone.now() > payment_deadline:
        order.status = 'canceled'
        order.save(update_fields=['status'])
        for item in order.items.all():
            if item.product_variant:
                item.product_variant.quantity = F('quantity') + item.quantity
                item.product_variant.save(update_fields=['quantity'])
            else:
                prod = Product.objects.filter(name=item.product_name).first()
                if prod:
                    prod.quantity = F('quantity') + item.quantity
                    prod.save(update_fields=['quantity'])
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = {key for key, _ in Order.STATUS_CHOICES}

        if new_status in valid_statuses and new_status != order.status:
            prev_status = order.status
            order.status = new_status
            order.save(update_fields=['status'])

            # 2) При платеже ничего не делаем — запасы уже зарезервированы
            # (УБРАН блок списания при paid)

            # 3) При ручной отмене возвращаем товары на склад
            if new_status == 'canceled' and prev_status in ('new', 'paid'):
                for item in order.items.all():
                    if item.product_variant:
                        item.product_variant.quantity = F('quantity') + item.quantity
                        item.product_variant.save(update_fields=['quantity'])
                    else:
                        prod = Product.objects.filter(name=item.product_name).first()
                        if prod:
                            prod.quantity = F('quantity') + item.quantity
                            prod.save(update_fields=['quantity'])

        return redirect('order_detail', order_id=order.id)

    return render(request, 'samal/order_detail.html', {
        'order': order,
        'payment_deadline': payment_deadline,
    })

# -------------  ОЧИСТКА СЕССИИ (по кнопке)  -----------------
def clear_order_session(request):
    request.session.pop("order_data", None)
    return redirect("category")
def services(request):
    services = Service.objects.all() 
    return render(request, 'samal/services.html', {'services': services})

def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug)
    # Будут доступны в шаблоне через service.variants.all()
    return render(request, 'samal/service_detail.html', {'service': service})

def service_variant_detail(request, service_slug, variant_slug):
    service = get_object_or_404(Service, slug=service_slug)
    variant = get_object_or_404(ServiceVariant, service=service, slug=variant_slug)
    images = variant.images.all()
    context = {
        'service': service,
        'variant': variant,
        'images': images
    }
    return render(request, 'samal/service_variant_detail.html', context)


from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail

import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def order_service_success(request, service_slug, variant_slug):
    """
    Показываем страницу «Ваш заказ принят» + кнопку «Скачать PDF»
    """
    service = get_object_or_404(Service, slug=service_slug)
    variant = get_object_or_404(ServiceVariant, service=service, slug=variant_slug)
    # убедимся, что invoice_data в сессии есть
    invoice = request.session.get('invoice_data')
    if not invoice:
        messages.error(request, "Нет данных для счёта.")
        return redirect('order_service_variant', service_slug=service_slug, variant_slug=variant_slug)

    return render(request, 'samal/order_service_success.html', {
        'service': service,
        'variant': variant,
    })

def order_service_variant(request, service_slug, variant_slug):
    service = get_object_or_404(Service, slug=service_slug)
    variant = get_object_or_404(ServiceVariant, service=service, slug=variant_slug)

    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        comment = request.POST.get('comment', '').strip()

        # Отправляем письмо админу
        subject = f"Новый заказ: {service.title} – {variant.title} от {name}"
        full_message = (
            f"Услуга: {service.title}\n"
            f"Вариант: {variant.title}\n\n"
            f"Имя: {name}\n"
            f"Email: {email}\n"
            f"Телефон: {phone}\n"
            f"Комментарий: {comment or '—'}\n"
        )
        send_mail(
            subject,
            full_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ORDER_EMAIL],
            fail_silently=False,
        )

        # Сохраняем данные в сессии
        request.session['invoice_data'] = {
            'service':       service.title,
            'variant':       variant.title,
            'name':          name,
            'email':         email,
            'phone':         phone,
            'comment':       comment,
            'creation_date': timezone.now().strftime("%d.%m.%Y %H:%M"),
            'address':       "Алматы, пр. Райымбека 221",
        }

        messages.success(request, "Ваш заказ принят! Счёт доступен для скачивания.")
        return redirect('order_service_success', service_slug=service_slug, variant_slug=variant_slug)

    return render(request, 'samal/order_service_variant.html', {
        'service': service,
        'variant': variant,
    })


def download_invoice(request):
    """
    Отдаём HTML‑счёт с кнопкой печати/скачать
    """
    data = request.session.get('invoice_data')
    if not data:
        messages.error(request, "Данные для счёта не найдены.")
        return redirect('category')

    return render(request, 'samal/invoice_service.html', data)
# --------------------------------------------------------------------------------------

from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from decimal import Decimal
from .models import Product, ProductVariant  # убедись, что импорт есть
import io

def invoice_view(request):
    order_data = request.session.get("order_data")
    if not order_data:
        return HttpResponse("No order data", status=400)

    items = _restore_items(order_data["cart_items"])

    ctx = {
        "cart_items": items,
        "total_price": Decimal(order_data["total_price"]),
        "name": order_data["name"],
        "email": order_data["email"],
        "phone": order_data["phone"],
        "address": order_data["address"],
        "comment": order_data["comment"],
        "order_id": order_data.get("order_id", ""),
        "creation_date": order_data.get("creation_date", ""),
    }
    return render(request, "samal/invoice_print.html", ctx)

def _restore_items(cart_items_serialized):
    """
    На вход получает список словарей:
    [
        {
            "product_name": "Товар A",
            "color": "Синий",
            "size": "L",
            "quantity": 10,
            "unit_price": "12345.00",
            "total_price": "123450.00",
        },
        …
    ]
    А возвращает список объектов (или просто тех же словарей), 
    удобных для рендеринга в шаблоне:
    """
    restored = []
    for x in cart_items_serialized:
        restored.append({
            "product_name": x["product_name"],
            "color": x["color"],
            "size": x["size"],
            "quantity": x["quantity"],
            "unit_price": Decimal(x["unit_price"]),
            "total_price": Decimal(x["total_price"]),
        })
    return restored

def invoice_view(request):
    order_data = request.session.get("order_data")
    if not order_data:
        return HttpResponse("No order data", status=400)

    # мы сохранили cart_items в виде списка dict-ов, но
    # функция _restore_items, если нужна, может восстанавливать объекты CartItem.
    # Если вам достаточно вывести их как есть (dict с полями), вы можете не вызывать _restore_items.
    items = order_data.get("cart_items", [])

    ctx = {
        "cart_items": items,
        "total_price": Decimal(order_data.get("total_price", "0")),
        "name": order_data.get("name", ""),
        "email": order_data.get("email", ""),
        "phone": order_data.get("phone", ""),
        "address": order_data.get("address", ""),
        "comment": order_data.get("comment", ""),
        "order_id": order_data.get("order_id", ""),
        "creation_date": order_data.get("creation_date", ""),
    }
    return render(request, "samal/invoice_print.html", ctx)