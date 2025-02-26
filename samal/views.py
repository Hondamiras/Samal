from django.shortcuts import get_list_or_404, redirect, render, get_object_or_404
from samal.models import Product, Category, ProductImage
from samal.forms import ContactForm
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
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

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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
    paginator = Paginator(products_list, 3)  # укажите нужное количество товаров на страницу
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

    context = {
        'product': product,
        'category': category,
        'product_images': product_images
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
