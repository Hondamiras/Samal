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

def home(request):
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'samal/home.html', context)


def about(request):
    return render(request, 'samal/about.html')


def category(request):
    # Получаем все категории
    categories = Category.objects.all()

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
    products_list = Product.objects.filter(category=category)
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

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    category = get_object_or_404(Category, slug=product.category.slug)
    product_images = product.product_images.all()
    wholesale_prices = product.wholesale_prices.all()
    
    # All variants for this product (color+size+quantity)
    product_variants_qs = product.variants.all()

    if product_variants_qs.exists():
        # Filter only colors and sizes actually present in the variants
        product_colors = ProductColor.objects.filter(
            product=product,
            id__in=product_variants_qs.values_list('color', flat=True)
        ).distinct()
        product_sizes = ProductSize.objects.filter(
            product=product,
            id__in=product_variants_qs.values_list('size', flat=True)
        ).distinct()
    else:
        product_colors = []
        product_sizes = []

    # Build a dictionary: { color_id: [ { "size_id": X, "size_name": "...", "quantity": n }, ... ], ... }
    grouped_variants = {}
    for variant in product_variants_qs:
        color_id = variant.color.id
        if color_id not in grouped_variants:
            grouped_variants[color_id] = []
        grouped_variants[color_id].append({
            'size_id': variant.size.id,
            'size_name': variant.size.size,  # or variant.size.display_name, etc.
            'quantity': variant.quantity
        })

    # Convert dict to JSON so the template can parse it
    variants_json = json.dumps(grouped_variants, ensure_ascii=False)

    # Check if user has liked this product
    session_key = get_session_key(request)  # your own session key function
    liked = Like.objects.filter(product=product, session_key=session_key).exists()

    context = {
        'product': product,
        'category': category,
        'product_images': product_images,
        'wholesale_prices': wholesale_prices,
        'product_colors': product_colors,
        'product_sizes': product_sizes,
        'liked': liked,
        'variants_json': variants_json,  # Pass the JSON into the template
    }
    return render(request, 'samal/product_detail.html', context)


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            subject = f'Новое сообщение от {name}'
            full_message = f"Сообщение от {name} ({email}):\n\n{message}"

            try:
                send_mail(
                    subject,
                    full_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL]
                )
                messages.success(request, 'Ваше сообщение успешно отправлено!')
            except Exception as e:
                messages.error(request, 'Произошла ошибка при отправке вашего сообщения. Попробуйте ещё раз позже.')
            return redirect('contact')
    else:
        form = ContactForm()
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

def order_view(request):
    session_key = get_session_key(request)
    cart = Cart.objects.filter(session_key=session_key).first()
    cart_items = cart.items.all() if cart else []
    total_price = sum(item.total_price for item in cart_items)

    if not cart_items:
        messages.error(request, "Корзина пуста")

    if request.method == 'POST':
        if total_price < 5000:
            messages.error(request, "Минимальная сумма заказа должна быть не менее 5000 ₸")
            return render(request, 'samal/order.html', {
                'cart_items': cart_items,
                'total_price': total_price,
            })

        # Собираем данные формы
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        comment = request.POST.get('comment', '')

        subject = f"Новый заказ от {name}"
        message_lines = [
            "Детали заказа:",
            "---------------------",
        ]

        for item in cart_items:
            if item.product_variant:
                product = item.product_variant.product
                color = item.product_variant.color.color if item.product_variant.color else "не указан"
                size = item.product_variant.size.size if item.product_variant.size else "не указан"
            else:
                product = item.product
                color = "не указан"
                size = "не указан"

            unit_price = get_unit_price(item)
            total = item_total(item)

            message_lines.append(
                f"ID: {product.id if product else '—'}\n"
                f"Название: {product.name if product else '—'}\n"
                f"Количество: {item.quantity} {product.get_unit_display() if product else ''}\n"
                f"Цвет: {color}\n"
                f"Размер: {size}\n"
                f"Цена за единицу: {unit_price} ₸\n"
                f"Итого: {total} ₸\n"
                "---------------------"
            )

        message_lines.append(f"Общая сумма заказа: {total_price} ₸")
        message_lines.extend([
            "",
            "Контактная информация:",
            f"Имя: {name}",
            f"Email: {email}",
            f"Телефон: {phone}",
            f"Адрес доставки: {address}",
            f"Комментарий: {comment}",
        ])

        full_message = "\n\n".join(message_lines)

        # Обрабатываем всё в атомарной транзакции
        with transaction.atomic():
            # Уменьшаем остатки по каждому товару/варианту
            for item in cart_items:
                if item.product_variant:
                    variant = item.product_variant
                    variant.quantity = F('quantity') - item.quantity
                    variant.save(update_fields=['quantity'])
                else:
                    product = item.product
                    product.quantity = F('quantity') - item.quantity
                    product.save(update_fields=['quantity'])

            # Отправляем уведомление на почту
            send_mail(
                subject,
                full_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ORDER_EMAIL],
            )

            # Очищаем корзину
            if cart:
                cart.delete()

        messages.success(request, "Ваш заказ отправлен. Мы свяжемся с вами в ближайшее время.")
        return redirect('order_success')

    return render(request, 'samal/order.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })
def order_success_view(request):
    return render(request, 'samal/order_success.html')

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


def order_service_variant(request, service_slug, variant_slug):
    service = get_object_or_404(Service, slug=service_slug)
    variant = get_object_or_404(ServiceVariant, service=service, slug=variant_slug)
    
    if request.method == 'POST':
        # Получение данных из формы заказа
        name = request.POST.get('name')
        user_email = request.POST.get('email')
        phone = request.POST.get('phone')
        comment = request.POST.get('comment', '')
        
        # Формирование темы письма
        subject = f"Новый заказ на услугу {service.title} - {variant.title} от {name}"
        
        # Сбор деталей заказа в сообщение
        message_lines = [
            "Детали заказа:",
            f"Услуга: {service.title}",
            f"Вариант услуги: {variant.title}",
            "",
            f"Имя: {name}",
            f"Email: {user_email}",
            f"Телефон: {phone}",
            f"Комментарий: {comment}",
        ]
        full_message = "\n\n".join(message_lines)
        
        # Отправка письма
        send_mail(
            subject,
            full_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ORDER_EMAIL],
            fail_silently=False,
        )
        
        # Вывод сообщения об успехе и редирект на страницу успешного оформления заказа
        messages.success(request, "Ваш заказ отправлен. Мы свяжемся с вами в ближайшее время.")
        return redirect('order_success')
    
    # При GET-запросе просто отображаем форму заказа
    context = {
        'service': service,
        'variant': variant,
    }
    return render(request, 'samal/order_service_variant.html', context)