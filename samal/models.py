from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import F
from smart_selects.db_fields import ChainedForeignKey
from django.utils import timezone

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('paid', 'Оплачен'),
        ('canceled', 'Отменён'),
        ('delivered', 'Доставлен'),
    ]

    # Информация о клиенте
    name       = models.CharField(max_length=255, verbose_name="Имя клиента")
    email      = models.EmailField(blank=True, verbose_name="Email клиента")
    phone      = models.CharField(max_length=50, verbose_name="Телефон клиента")
    address    = models.TextField(blank=True, verbose_name="Адрес доставки")
    comment    = models.TextField(blank=True, verbose_name="Комментарий клиента")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status     = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус заказа"
    )
    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Итоговая сумма"
    )

    ORDER_SOURCE_CHOICES = [
    ('site', 'Сайт'),
    ('direct', 'Прямая продажа'),
    ]
    source = models.CharField(
        max_length=10,
        choices=ORDER_SOURCE_CHOICES,
        default='site',
        verbose_name='Источник заказа'
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} от {self.created_at.strftime('%d.%m.%Y %H:%M')} — {self.get_status_display()}"

    @property
    def is_expired(self):
        # True, если прошло более 24 ч. и статус всё ещё 'new'
        if self.status == 'new':
            return timezone.now() > self.created_at + timezone.timedelta(hours=24)
        return False

    def mark_expired(self):
        # Помечает заказ как отменённый, но не трогает запасы
        if self.is_expired:
            self.status = 'canceled'
            self.save(update_fields=['status'])

class OrderItem(models.Model):
    order            = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product_variant  = models.ForeignKey(
        'ProductVariant', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Вариант товара"
    )
    product_name     = models.CharField(max_length=255, verbose_name="Название товара")
    quantity         = models.PositiveIntegerField(default=1, verbose_name="Количество")
    unit_price       = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу")
    total_price      = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Итоговая цена позиции")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"

    def __str__(self):
        return f"{self.product_name} — {self.quantity} шт. — {self.total_price} ₸"

    def save(self, *args, **kwargs):
        # 1) считаем, на сколько изменилось количество
        if self.pk:
            old = OrderItem.objects.get(pk=self.pk)
            delta = self.quantity - old.quantity
        else:
            delta = self.quantity

        # 2) проверяем остаток
        variant = self.product_variant
        if variant.quantity is not None and variant.quantity < delta:
            raise ValidationError(
                f"Недостаточно товара {variant} на складе (осталось {variant.quantity})."
            )

        # 3) атомарно списываем со склада
        ProductVariant.objects.filter(pk=variant.pk).update(
            quantity=F('quantity') - delta
        )

        # 4) сохраняем саму позицию
        super().save(*args, **kwargs)

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='URL')
    image = models.ImageField(upload_to='category_images/', blank=True, null=True, verbose_name='Изображение')
    TYPE_CHOICES = [
        ('knitted_fabric', 'Трикотажное полотно'),
        ('knitwear_product', 'Готовое изделие из трикотажа'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='knitted_fabric', verbose_name='Тип продукта')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='URL')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True, verbose_name='Изображение')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', blank=True, null=True)
    GENDER_CHOICES = [
        ('unisex', 'Унисекс'),
        ('male', 'Мужской'),
        ('female', 'Женский'),
        ('children', 'Детский'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex', verbose_name='Пол')
    UNIT_CHOICES = [
        ('pcs', 'шт'),
        ('kg', 'кг'),
    ]
    unit = models.CharField(
        max_length=3,
        choices=UNIT_CHOICES,
        default='pcs',
        verbose_name='Единица измерения'
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    description = models.TextField(verbose_name='Описание', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    AVAILABILITY_CHOICES = [
        ('in_stock', 'В наличии'),
        ('on_order', 'Под заказ'),
    ]
    availability = models.CharField(
        max_length=10,
        choices=AVAILABILITY_CHOICES,
        default='in_stock',
        verbose_name='Наличие'
    )
    expected_delivery = models.CharField(max_length=50, blank=True, verbose_name='Срок поставки')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

class WholesalePrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wholesale_prices', verbose_name='Продукт')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Оптовая цена')

    def __str__(self):
        return f'{self.quantity} {self.product.unit} – {self.price}$'

    class Meta:
        verbose_name = 'Оптовая цена'
        verbose_name_plural = 'Оптовые цены'

# Модели для базовых вариантов: цвет и размер.
class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors', verbose_name='Продукт')
    color = models.CharField(max_length=50, verbose_name='Цвет')
    # Запас для цвета можно задать отдельно в вариантах, поэтому здесь поле можно не использовать

    def __str__(self):
        return self.color

    class Meta:
        verbose_name = 'Цвет продукта'
        verbose_name_plural = 'Цвета продуктов'

class ProductSize(models.Model):
    # Задаём константу порядка
    SIZE_ORDER = [
        '5XS', '4XS', '3XS', '2XS', 
        'XS', 'S', 'M', 'L', 'XL', 
        '2XL', '3XL', '4XL', '5XL', 
        '6XL', '7XL', '8XL', '9XL', '10XL'
    ]
    # Генерируем список кортежей для choices
    SIZE_CHOICES = [(size, size) for size in SIZE_ORDER]

    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='sizes', 
        verbose_name='Продукт'
    )
    size = models.CharField(
        max_length=50, 
        choices=SIZE_CHOICES, 
        verbose_name='Размер'
    )

    def __str__(self):
        return self.size

    class Meta:
        verbose_name = 'Размер продукта'
        verbose_name_plural = 'Размеры продуктов'

# Новый вариант товара, связывающий продукт, цвет и размер и хранящий запас (stock) для конкретной комбинации.
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name='Продукт')
    color   = ChainedForeignKey(
        ProductColor,
        chained_field="product",
        chained_model_field="product",
        show_all=False,
        auto_choose=True,
    )
    size    = ChainedForeignKey(
        ProductSize,
        chained_field="product",
        chained_model_field="product",
        show_all=False,
        auto_choose=True,
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество', blank=True, null=True)

    def __str__(self):
        return f"{self.color} – {self.size}"

    class Meta:
        verbose_name = "Вариант товара"
        verbose_name_plural = "Варианты товаров"
        unique_together = ("product", "color", "size")

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images', verbose_name='Продукт')
    image = models.ImageField(upload_to='product_images/', verbose_name='Изображение продукта')

    def __str__(self):
        return f"Изображение продукта {self.product.name}"

    class Meta:
        verbose_name = 'Изображение продукта'
        verbose_name_plural = 'Изображения продуктов'

class Like(models.Model):
    session_key = models.CharField(max_length=40, verbose_name="Идентификатор сессии")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата лайка")

    def __str__(self):
        return f"Лайк для {self.product.name} с сессией {self.session_key}"

    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        unique_together = ('session_key', 'product')

class Cart(models.Model):
    session_key = models.CharField(max_length=40, unique=True, verbose_name="Идентификатор сессии")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"Корзина с сессией {self.session_key}"

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

# Модель CartItem, которая теперь ссылается на конкретный вариант товара
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="Корзина")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Вариант товара")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        if self.product_variant:
            return f"{self.product_variant.product.name} – {self.product_variant.color.color} – {self.product_variant.size.size}"
        return "Товар в корзине"

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзинах'
        unique_together = ('cart', 'product_variant')

    @property
    def price_to_use(self):
        if self.product_variant:
            # Фильтруем оптовые цены: выбираем те записи,
            # где значение поля quantity (минимальное количество) меньше или равно количеству в корзине.
            wholesale = self.product_variant.product.wholesale_prices.filter(
                quantity__lte=self.quantity
            ).order_by('-quantity').first()
            if wholesale:
                return wholesale.price
            return self.product_variant.product.price
        return 0



    @property
    def total_price(self):
        return self.price_to_use * self.quantity

class Service(models.Model):
    title = models.CharField(max_length=200, help_text="Название услуги")
    slug = models.SlugField(
        unique=True,
        help_text="Уникальный идентификатор для URL, например: sewing, embroidery, printing"
    )
    description = models.TextField(help_text="Подробное описание услуги")
    image = models.ImageField(
        upload_to='services/',
        blank=True,
        null=True,
        help_text="Изображение услуги"
    )

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return self.title
    
class ServiceVariant(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="variants")
    slug = models.SlugField(help_text="Уникальный идентификатор для варианта, например: option1")
    title = models.CharField(max_length=200, help_text="Название варианта услуги")
    description = models.TextField(help_text="Подробное описание варианта")
    image = models.ImageField(upload_to="services/variants/", blank=True, null=True, help_text="Изображение варианта")

    class Meta:
        verbose_name = "Вариант услуги"
        verbose_name_plural = "Варианты услуг"

    def __str__(self):
        return f"{self.service.title} - {self.title}"

class ServiceVariantImage(models.Model):
    variant = models.ForeignKey(ServiceVariant, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="services/variants/images/", help_text="Изображение варианта услуги")

    class Meta:
        verbose_name = "Изображение варианта услуги"
        verbose_name_plural = "Изображения вариантов услуг"

    def __str__(self):
        return f"Изображение для {self.variant.title}"