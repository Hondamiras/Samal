from django.shortcuts import get_list_or_404, render, get_object_or_404
from samal.models import Product, Category


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

def category_detail(request, slug):

    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)

    context = {
        'categories': category,
        'products': products
    }

    return render(request, 'samal/category_detail.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    context = {
        'product': product
    }

    return render(request, 'samal/product_detail.html', context)

def contact(request):
    return render(request, 'samal/contact.html')