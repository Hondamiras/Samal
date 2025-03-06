from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='URL')
    image = models.ImageField(upload_to='category_images/', blank=True, null=True, verbose_name='Изображение')

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
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Оптовая цена', blank=True, null=True)
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
    expected_delivery = models.CharField(
    max_length=50,
    blank=True,
    verbose_name='Срок поставки'
)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Продукт', related_name='product_images')
    image = models.ImageField(upload_to='product_images/', verbose_name='Изображениe продукта')

    def __str__(self):
        return f"Изображение продукта {self.product.name}"
    
    class Meta:
        verbose_name = 'Изображение продукта'
        verbose_name_plural = 'Изображения продуктов'

class Like(models.Model):
    session_key = models.CharField(max_length=40, verbose_name="Идентификатор сессии")
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name="Продукт")
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
        # Sum the CartItem `total_price` property
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name="Корзина", related_name="items")
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name="Продукт")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
    
    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзинах'
        unique_together = ('cart', 'product')

    @property
    def price_to_use(self):
        """Use wholesale price if quantity ≥ 100, otherwise regular price."""
        if self.quantity >= 100 and self.product.wholesale_price is not None:
            return self.product.wholesale_price
        return self.product.price or 0

    @property
    def total_price(self):
        return self.price_to_use * self.quantity
