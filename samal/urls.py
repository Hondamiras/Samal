from django.urls import path
from samal.views import *

urlpatterns = [
    path('', home, name='home'),
    path('category/', category, name='category'),
    path('category/<slug:slug>/', category_detail, name='category_detail'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    path('contact/', contact_view, name='contact'),
]
