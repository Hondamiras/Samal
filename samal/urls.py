from django.urls import path
from samal.views import *

urlpatterns = [
    path('', home, name='home'),
    path('category/', category, name='category'),
    path('search/', product_search, name='search'),
    path('category/<slug:slug>/', category_detail, name='category_detail'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    path('contact/', contact_view, name='contact'),
    path('about/', about, name='about'),
    path('liked/', liked_products, name='liked_products'),
    path('toggle_like/<slug:product_slug>/', toggle_like, name='toggle_like'),
    path('cart_detail/', cart_detail, name='cart_detail'),
    path('add_to_cart/<slug:product_slug>/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update-quantity/', update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove-item-ajax/', remove_cart_item_ajax, name='remove_cart_item_ajax'),
    path('cart/clear/', clear_cart, name='clear_cart'),
]
