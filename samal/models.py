from django.db import models

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
        return f'{self.product.name} – {self.color}'

    class Meta:
        verbose_name = 'Цвет продукта'
        verbose_name_plural = 'Цвета продуктов'


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes', verbose_name='Продукт')
    size = models.CharField(max_length=50, verbose_name='Размер')
    # Аналогично, запас для размера хранится в вариантах

    def __str__(self):
        return f'{self.product.name} – {self.size}'

    class Meta:
        verbose_name = 'Размер продукта'
        verbose_name_plural = 'Размеры продуктов'


# Новый вариант товара, связывающий продукт, цвет и размер и хранящий запас (stock) для конкретной комбинации.
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name='Продукт')
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, verbose_name='Цвет')
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, verbose_name='Размер')
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество', blank=True, null=True)

    def __str__(self):
        return f"{self.color.color} – {self.size.size}"

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
