from django.urls import path
from . import views

app_name = 'direct_sales'

urlpatterns = [
    # … other patterns …
    path('', views.direct_orders_list, name='direct_orders_list'),
]
