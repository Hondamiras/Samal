from django.http import JsonResponse
from django.shortcuts import get_list_or_404, redirect, render, get_object_or_404
from samal.models import Cart, CartItem, Like, Product, Category, ProductImage
from samal.forms import ContactForm
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

# Create your views here.
def get_session_key(request):
    """
    Получаем идентификатор сессии, если его нет — создаём новую сессию.
    """
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    return session_key

def home(request):
    categories = Category.objects.all()

    context = {
        'categories': categories,
    }

    return render(request, 'samal/home.html', context)

def category(request):

    categories = get_list_or_404(Category)

    context = {
        'categories': categories
    }

    return render(request, 'samal/category.html', context)

def product_search(request):
    query = request.GET.get('q', '').strip()
    products_list = Product.objects.all()
    
    if query:
        products_list = products_list.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        ).distinct()

    # Пагинация
    paginator = Paginator(products_list, 6)  # укажите нужное количество товаров на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj.object_list,
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'samal/search_results.html', context)

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    # Получаем все товары выбранной категории
    products_list = Product.objects.filter(category=category)

    # Считываем выбранный способ сортировки из GET-параметров
    sort_option = request.GET.get('sort', '')

    # Применяем сортировку в зависимости от выбранного варианта
    if sort_option == 'price_asc':
        products_list = products_list.order_by('price')
    elif sort_option == 'price_desc':
        products_list = products_list.order_by('-price')
    elif sort_option == 'newest':
        # Предполагается, что поле created_at хранит дату создания товара
        products_list = products_list.order_by('-created_at')
    # Если никакая сортировка не выбрана, оставляем порядок по умолчанию (например, по id)

    # Пагинация
    paginator = Paginator(products_list, 6)  # укажите нужное количество товаров на страницу
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
    }

    return render(request, 'samal/category_detail.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    category = get_object_or_404(Category, slug=product.category.slug)
    product_images = product.product_images.all()
    
    # Get or create the session key
    session_key = get_session_key(request)
    liked = Like.objects.filter(product=product, session_key=session_key).exists()

    context = {
        'product': product,
        'category': category,
        'product_images': product_images,
        'liked': liked,
    }
    return render(request, 'samal/product_detail.html', context)


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Получение данных из формы
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            # Дополнительная обработка данных или отправка письма.
            subject = f'Новое сообщение от {name}'
            full_message = f"Сообщение от {name} ({email}):\n\n{message}"
            
            try:
                send_mail(
                    subject,
                    full_message,
                    settings.DEFAULT_FROM_EMAIL,  # Убедитесь, что это значение установлено в settings.py
                    [settings.CONTACT_EMAIL]       # CONTACT_EMAIL должен быть определён в settings или заменён на нужный email получателя
                )
                messages.success(request, 'Ваше сообщение успешно отправлено!')
            except Exception as e:
                messages.error(request, 'Произошла ошибка при отправке вашего сообщения. Попробуйте ещё раз позже.')
            
            return redirect('contact')  # Измените 'contact' на соответствующее имя URL в вашем проекте
    else:
        form = ContactForm()
    
    return render(request, 'samal/contact.html', {'form': form})

def about(request):
    return render(request, 'samal/about.html')






# Представление для переключения лайка (добавление/удаление)
def toggle_like(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    session_key = get_session_key(request)
    like, created = Like.objects.get_or_create(session_key=session_key, product=product)
    if not created:
        # Если лайк уже существует — удаляем его (отмена лайка)
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'success': True, 'liked': liked})

# Представление для отображения списка понравившихся товаров
def liked_products(request):
    session_key = request.session.session_key
    likes = Like.objects.filter(session_key=session_key) if session_key else []
    return render(request, 'samal/liked_products.html', {'likes': likes})

# Добавление товара в корзину
def add_to_cart(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    session_key = get_session_key(request)
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        # Если товар уже есть в корзине, увеличиваем количество
        cart_item.quantity += 1
        cart_item.save()
    # Return JSON response for AJAX calls
    return JsonResponse({
        'success': True,
        'message': 'Товар успешно добавлен в корзину',
        'quantity': cart_item.quantity,
    })

# Отображение корзины
def cart_detail(request):
    session_key = get_session_key(request)
    cart = Cart.objects.filter(session_key=session_key).first()
    cart_items = cart.items.all() if cart else []

    # Apply the same wholesale logic when calculating total
    total_price = sum(
        (item.product.wholesale_price if item.quantity >= 100 else item.product.price) * item.quantity
        for item in cart_items
    ) if cart_items else 0

    return render(request, 'samal/cart_detail.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price
    })


# Удаление товара из корзины
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('cart_detail')


def update_cart_quantity(request):
    """
    Updates the quantity of a specific CartItem based on the 'action' POST parameter.
    Expects:
      - item_id (CartItem ID)
      - action ('plus', 'minus', or 'set')
      - quantity (for 'set' action)
    Returns JSON with success, new quantity, item_total, and cart_total.
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        session_key = get_session_key(request)

        # Try to fetch the specific cart item for this session
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

        # If quantity drops to 0 or below, remove the item
        if cart_item.quantity <= 0:
            cart_item.delete()
            new_quantity = 0
            item_total = 0
            cart_total = sum(
                (ci.product.wholesale_price if ci.quantity >= 100 else ci.product.price) * ci.quantity
                for ci in CartItem.objects.filter(cart__session_key=session_key)
            )
        else:
            cart_item.save()
            new_quantity = cart_item.quantity

            # Decide whether to use regular price or wholesale price
            price_to_use = (
                cart_item.product.wholesale_price 
                if cart_item.quantity >= 100 
                else cart_item.product.price
            )

            item_total = price_to_use * new_quantity

            # Recalculate the cart total with the same logic for each item
            cart = cart_item.cart
            cart_total = sum(
                (
                    ci.product.wholesale_price if ci.quantity >= 100 else ci.product.price
                ) * ci.quantity
                for ci in cart.items.all()
            )
        
        is_wholesale = cart_item.quantity >= 100 and cart_item.product.wholesale_price is not None

        return JsonResponse({
            'success': True,
            'quantity': new_quantity,
            'item_total': item_total,
            'cart_total': cart_total,
            'is_wholesale': is_wholesale,
            'unit_price': price_to_use,
            'wholesale_price': cart_item.product.wholesale_price,
            'regular_price': cart_item.product.price
        })
    else:
        return JsonResponse({'success': False, 'error': 'POST должен быть'}, status=405)


def remove_cart_item_ajax(request):
    """
    Removes a single item from the cart.
    Expects:
      - item_id
    Returns JSON with success and updated cart_total.
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        session_key = get_session_key(request)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__session_key=session_key)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'CartItem not found'}, status=404)

        # Calculate new total
        cart = Cart.objects.filter(session_key=session_key).first()
        cart_total = 0
        if cart:
            cart_total = sum(ci.product.price * ci.quantity for ci in cart.items.all())

        return JsonResponse({
            'success': True,
            'cart_total': cart_total
        })
    else:
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)


def clear_cart(request):
    """
    Clears the entire cart for the current session.
    Returns JSON with success.
    """
    if request.method == 'POST':
        session_key = get_session_key(request)
        Cart.objects.filter(session_key=session_key).delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'POST должен быть'}, status=405)
