from django.urls import path
from samal.views import *

urlpatterns = [
    # Основной каталог (главная страница)
    path('', category, name='category'),

    # Поиск и страницы категорий/товаров
    path('search/', product_search, name='search'),
    path('category/<slug:slug>/', category_detail, name='category_detail'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),

    # Контакты и информация о нас
    path('contact/', contact_view, name='contact'),
    # path('about/', about, name='about'),

    # Избранное, корзина и взаимодействие с ними
    path('liked/', liked_products, name='liked_products'),
    path('favorites/remove/<slug:slug>/', remove_favorite, name='remove_favorite'),
    path('toggle_like/<slug:product_slug>/', toggle_like, name='toggle_like'),
    path('cart_detail/', cart_detail, name='cart_detail'),
    path('add_to_cart/<slug:product_slug>/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update-quantity/', update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove-item-ajax/', remove_cart_item_ajax, name='remove_cart_item_ajax'),
    path('cart/clear/', clear_cart, name='clear_cart'),

    # Заказы
    path('order/', order_view, name='order'),
    path('order/success/', order_success_view, name='order_success'),

    # Услуги и подробное описание услуг
    path('services/', services, name='services'),
    path('services/<slug:slug>/', service_detail, name='service_detail'),
    path('services/<slug:service_slug>/<slug:variant_slug>/', service_variant_detail, name='service_variant_detail'),
    path('download-invoice/', download_invoice, name='download_invoice'),
    path('order/success/<slug:service_slug>/<slug:variant_slug>/', order_service_success, name='order_service_success'),

    # Оформление заказа конкретного варианта услуги
    path('order/<slug:service_slug>/<slug:variant_slug>/', order_service_variant, name='order_service_variant'),
    path('order/clear/', clear_order_session, name='order_clear'),
    path('order/invoice/', invoice_view, name='order_invoice')
]
