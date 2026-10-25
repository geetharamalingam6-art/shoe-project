from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image_static = models.CharField(max_length=255, blank=True, help_text="Static image path for category card")
    image = models.ImageField(upload_to='categories/', null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    brand = models.CharField(max_length=100, default="Comfy Steps")
    style_type = models.CharField(max_length=100, default="Trainers")
    sizes = models.CharField(max_length=200, default="Adult UK(6), Adult UK(7)")
    colors = models.CharField(max_length=200, default="Black, Brown, White")
    mrp_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    image_static = models.CharField(max_length=255, blank=True, help_text="Fallback static image path")
    description = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    is_featured = models.BooleanField(default=True)
    is_trending = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def price(self):
        return self.mrp_price

    @property
    def final_price(self):
        if self.discount_price:
            return self.discount_price
        return self.mrp_price

    @property
    def discount_percent(self):
        if self.discount_price and self.mrp_price > self.discount_price:
            return int(((self.mrp_price - self.discount_price) / self.mrp_price) * 100)
        return 0

    @property
    def discount_amount(self):
        if self.discount_price and self.mrp_price > self.discount_price:
            return int(self.mrp_price - self.discount_price)
        return 0

    def __str__(self):
        return self.name


class Slide(models.Model):
    title = models.CharField(max_length=150, default="Flat 50% Sale")
    subtitle = models.CharField(max_length=150, default="Kids Shoes")
    button_text = models.CharField(max_length=50, default="Shop Now")
    button_url = models.CharField(max_length=200, default="/category/kids/")
    image_static = models.CharField(max_length=255, default="shoe/images/hero_kids.jpg")
    image = models.ImageField(upload_to='slides/', null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} - {self.subtitle}"


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.product.final_price * self.quantity


class Order(models.Model):
    PAYMENT_PENDING = 'pending'
    PAYMENT_PAID = 'paid'
    PAYMENT_FAILED = 'failed'
    PAYMENT_CHOICES = [
        (PAYMENT_PENDING, 'Pending'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_FAILED, 'Failed'),
    ]

    order_number = models.CharField(max_length=20, unique=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=15)
    shipping_address = models.TextField()
    billing_address = models.TextField()
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default=PAYMENT_PENDING)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    razorpay_order_id = models.CharField(max_length=40, blank=True)
    razorpay_payment_id = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.full_name}"

    @property
    def is_paid(self):
        return self.payment_status == self.PAYMENT_PAID

    @property
    def masked_card(self):
        if self.card_last4:
            return f"**** **** **** {self.card_last4}"
        return "—"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    image_static = models.CharField(max_length=255, blank=True)
    size = models.CharField(max_length=20, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
