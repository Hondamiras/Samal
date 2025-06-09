from django.urls import path
from samal.views import (
    category,
    product_search,
    category_detail,
    product_detail,
    contact_view,
    liked_products,
    remove_favorite,
    toggle_like,
    cart_detail,
    add_to_cart,
    remove_from_cart,
    update_cart_quantity,
    remove_cart_item_ajax,
    clear_cart,
    order_view,
    order_success_view,
    services,
    service_detail,
    service_variant_detail,
    download_invoice,
    order_service_success,
    order_service_variant,
    clear_order_session,
    invoice_view,
    orders_list_view,
    order_detail_view,
)

urlpatterns = [
    # ----------------------------------------
    # 1. Основной каталог (главная страница)
    # ----------------------------------------
    path("", category, name="category"),

    # ----------------------------------------
    # 2. Поиск и страницы категорий/товаров
    # ----------------------------------------
    path("search/", product_search, name="search"),
    path("category/<slug:slug>/", category_detail, name="category_detail"),
    path("product/<slug:slug>/", product_detail, name="product_detail"),

    # ----------------------------------------
    # 3. Контакты и информация о нас
    # ----------------------------------------
    path("contact/", contact_view, name="contact"),
    # path("about/", about, name="about"),

    # ----------------------------------------
    # 4. Избранное, корзина и взаимодействие с ними
    # ----------------------------------------
    path("liked/", liked_products, name="liked_products"),
    path("favorites/remove/<slug:slug>/", remove_favorite, name="remove_favorite"),
    path("toggle_like/<slug:product_slug>/", toggle_like, name="toggle_like"),

    path("cart_detail/", cart_detail, name="cart_detail"),
    path("add_to_cart/<slug:product_slug>/", add_to_cart, name="add_to_cart"),
    path("remove_from_cart/<int:item_id>/", remove_from_cart, name="remove_from_cart"),
    path("cart/update-quantity/", update_cart_quantity, name="update_cart_quantity"),
    path("cart/remove-item-ajax/", remove_cart_item_ajax, name="remove_cart_item_ajax"),
    path("cart/clear/", clear_cart, name="clear_cart"),

    # ----------------------------------------
    # 5. Оформление заказа (корзина → страница заказа)
    # ----------------------------------------
    # 5.1. Страница оформления заказа
    path("order/", order_view, name="order"),
    # 5.2. Страница «успешно оформлен заказ»
    path("order/success/", order_success_view, name="order_success"),

    # ----------------------------------------
    # 6. Услуги и подробное описание услуг
    # ----------------------------------------
    path("services/", services, name="services"),
    path("services/<slug:slug>/", service_detail, name="service_detail"),
    path(
        "services/<slug:service_slug>/<slug:variant_slug>/",
        service_variant_detail,
        name="service_variant_detail",
    ),
    path("download-invoice/", download_invoice, name="download_invoice"),

    # ----------------------------------------
    # 7. Специфичные маршруты для оформления заказа услуги
    # ----------------------------------------
    # 7.1. Успех заказа услуги (если нужно показывать отдельную страницу)
    path(
        "order/success/<slug:service_slug>/<slug:variant_slug>/",
        order_service_success,
        name="order_service_success",
    ),
    # 7.2. Формирование страницы заказа конкретного варианта услуги
    path(
        "order/<slug:service_slug>/<slug:variant_slug>/",
        order_service_variant,
        name="order_service_variant",
    ),
    # 7.3. Очистка сессии заказа услуги (по необходимости)
    path("order/clear/", clear_order_session, name="order_clear"),
    # 7.4. Страница просмотра/скачивания счёта-фактуры (invoice)
    path("order/invoice/", invoice_view, name="order_invoice"),

    # ----------------------------------------
    # 8. API для менеджерского просмотра заказов
    # ----------------------------------------
    path("orders/", orders_list_view, name="orders_list"),
    path("orders/<int:order_id>/", order_detail_view, name="order_detail"),
]
