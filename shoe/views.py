from django.conf import settings

try:
    import razorpay
    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )
except ImportError:
    razorpay = None
    client = None

import logging
import re
import smtplib
import uuid

from requests.exceptions import RequestException
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.views.decorators.http import require_POST
from .models import Category, Product, Slide, CartItem, Order, OrderItem

logger = logging.getLogger(__name__)

DEFAULT_SLIDES = [
    {
        'title': 'Flat 50% Sale',
        'subtitle': 'Kids Shoes',
        'button_text': 'Shop Now',
        'button_url': '/category/kids/',
        'image_static': 'shoe/images/hero_kids.jpg',
    },
    {
        'title': 'Trending Pastel',
        'subtitle': "Women's Collection",
        'button_text': 'Shop Now',
        'button_url': '/category/womens/',
        'image_static': 'shoe/images/hero_womens.jpg',
    },
    {
        'title': 'Turbo High-Speed',
        'subtitle': "Men's Sneakers",
        'button_text': 'Shop Now',
        'button_url': '/category/mens/',
        'image_static': 'shoe/images/hero_mens.jpg',
    },
    {
        'title': 'Exclusive Drop',
        'subtitle': 'Streetwear Brands',
        'button_text': 'Shop Now',
        'button_url': '/category/brands/',
        'image_static': 'shoe/images/hero_brands.jpg',
    },
]

DEFAULT_CATEGORIES = [
    {'name': "Women's", 'slug': 'womens', 'image_static': 'shoe/images/womens.png'},
    {'name': "Men's", 'slug': 'mens', 'image_static': 'shoe/images/mens.png'},
    {'name': "Kids'", 'slug': 'kids', 'image_static': 'shoe/images/kids.png'},
    {'name': 'Brands', 'slug': 'brands', 'image_static': 'shoe/images/hero_brands.jpg'},
    {'name': 'Offers', 'slug': 'offers', 'image_static': 'shoe/images/hero_womens.jpg'},
]

SAMPLE_PRODUCTS = [
    # ==================== MENS (12 Products) ====================
    {
        'name': "Harlan Mens Tan Boat Shoe",
        'brand': "Comfy Steps",
        'category_slug': 'mens',
        'style_type': "New Arrivals",
        'sizes': "Adult UK(6), Adult UK(7)",
        'colors': "Black, Brown, White",
        'mrp_price': 2799,
        'discount_price': None,
        'image_static': 'shoe/images/men1.png',
        'description': "Premium tan boat shoe crafted for casual comfort and timeless style.",
        'rating': 5.0,
    },
    {
        'name': "Weaver Mens Lace Up Trainer",
        'brand': "Becket",
        'category_slug': 'mens',
        'style_type': "Trainers",
        'sizes': "Adult UK(5), Adult UK(6)",
        'colors': "Black, Red, White",
        'mrp_price': 1799,
        'discount_price': 1499,
        'image_static': 'shoe/images/men11.png',
        'description': "Lightweight lace up trainer designed for everyday active wear.",
        'rating': 4.8,
    },
    {
        'name': "Doubal Strap Sandals",
        'brand': "Comfy Steps",
        'category_slug': 'mens',
        'style_type': "Sandals",
        'sizes': "Adult UK(6), Adult UK(7)",
        'colors': "Black, Brown, White",
        'mrp_price': 2999,
        'discount_price': None,
        'image_static': 'shoe/images/men3.png',
        'description': "Comfortable double strap sandals for warm weather outings.",
        'rating': 4.0,
    },
    {
        'name': "Lustral white Leather Slippers",
        'brand': "Comfy Steps",
        'category_slug': 'mens',
        'style_type': "Slippers",
        'sizes': "Adult UK(4), Adult UK(5)",
        'colors': "Brown, White",
        'mrp_price': 1995,
        'discount_price': None,
        'image_static': 'shoe/images/men4.png',
        'description': "Luxurious white leather slippers for effortless indoor and outdoor relaxation.",
        'rating': 5.0,
    },
    {
        'name': "Classic Leather Boots",
        'brand': "Kickers",
        'category_slug': 'mens',
        'style_type': "Boots",
        'sizes': "Adult UK(6), Adult UK(7)",
        'colors': "Black, Brown",
        'mrp_price': 3499,
        'discount_price': 2999,
        'image_static': 'shoe/images/men5.png',
        'description': "Rugged and durable leather boots built for all terrains.",
        'rating': 4.9,
    },
    {
        'name': "Urban Street Canvas",
        'brand': "Lambretta",
        'category_slug': 'mens',
        'style_type': "Canvas",
        'sizes': "Adult UK(5), Adult UK(6)",
        'colors': "Blue, Black, Grey",
        'mrp_price': 1599,
        'discount_price': 1299,
        'image_static': 'shoe/images/men6.png',
        'description': "Trendy streetwear canvas shoes for casual weekend looks.",
        'rating': 4.7,
    },
    {
        'name': "Superhero Junior Sneaker",
        'brand': "Marvel",
        'category_slug': 'mens',
        'style_type': "Trainers",
        'sizes': "Junior UK(3), Junior UK(4)",
        'colors': "Red, Blue, Yellow",
        'mrp_price': 1299,
        'discount_price': None,
        'image_static': 'shoe/images/men7.png',
        'description': "Fun and vibrant superhero themed sneakers for young fans.",
        'rating': 4.8,
    },
    {
        'name': "Summer Beach Slip-On",
        'brand': "Totes",
        'category_slug': 'mens',
        'style_type': "Summer Shop",
        'sizes': "Adult UK(4), Adult UK(5)",
        'colors': "Blue, Green, Orange",
        'mrp_price': 899,
        'discount_price': None,
        'image_static': 'shoe/images/men8.png',
        'description': "Lightweight slip-ons ideal for beach days and summer lounging.",
        'rating': 4.6,
    },
    {
        'name': "Flex Advantage Trainer",
        'brand': "Skechers",
        'category_slug': 'mens',
        'style_type': "Trainers",
        'sizes': "Adult UK(6), Adult UK(7)",
        'colors': "Black, Grey, Blue",
        'mrp_price': 3999,
        'discount_price': 3499,
        'image_static': 'shoe/images/men9.png',
        'description': "High-flex athletic trainers with superior memory foam cushioning.",
        'rating': 5.0,
    },
    {
        'name': "Formal Oxford Shoes",
        'brand': "Becket",
        'category_slug': 'mens',
        'style_type': "New Arrivals",
        'sizes': "Adult UK(6), Adult UK(7)",
        'colors': "Black, Brown",
        'mrp_price': 4599,
        'discount_price': 3999,
        'image_static': 'shoe/images/men10.png',
        'description': "Impeccably tailored leather Oxford shoes for formal occasions.",
        'rating': 4.9,
    },
    {
        'name': "Casual Slip-On Loafer",
        'brand': "Lambretta",
        'category_slug': 'mens',
        'style_type': "Canvas",
        'sizes': "Adult UK(5), Adult UK(6)",
        'colors': "Brown, Grey, White",
        'mrp_price': 2199,
        'discount_price': 1799,
        'image_static': 'shoe/images/men11.png',
        'description': "Effortless slip-on loafers combining breathability and comfort.",
        'rating': 4.7,
    },
    {
        'name': "Waterproof Rain Boots",
        'brand': "Totes",
        'category_slug': 'mens',
        'style_type': "Boots",
        'sizes': "Adult UK(6), Adult UK(7)",
        'colors': "Black, Green, Grey",
        'mrp_price': 2799,
        'discount_price': None,
        'image_static': 'shoe/images/men12.png',
        'description': "Heavy-duty waterproof rain boots to keep your feet dry in style.",
        'rating': 4.8,
    },

    # ==================== WOMENS (12 Products) ====================
    {
        'name': "Ophelia Silver Diamante Heel",
        'brand': "Comfy Steps",
        'category_slug': 'womens',
        'style_type': "New Arrivals",
        'sizes': "Adult UK(4), Adult UK(5)",
        'colors': "White, Grey, Black",
        'mrp_price': 2499,
        'discount_price': 1999,
        'image_static': 'shoe/images/hero_womens.jpg',
        'description': "Exquisite silver diamante heel for special occasions and elegant styling.",
        'rating': 4.9,
    },
    {
        'name': "Billie women's silver",
        'brand': "Becket",
        'category_slug': 'womens',
        'style_type': "Trainers",
        'sizes': "Adult UK(4), Adult UK(5)",
        'colors': "White, Grey",
        'mrp_price': 1999,
        'discount_price': None,
        'image_static': 'shoe/images/new1.jpg',
        'description': "Sleek silver finish casual sneakers for everyday comfort.",
        'rating': 4.8,
    },
    {
        'name': "Black Block Heel Sandals",
        'brand': "Comfy Steps",
        'category_slug': 'womens',
        'style_type': "Sandals",
        'sizes': "Adult UK(5), Adult UK(6)",
        'colors': "Black, Brown",
        'mrp_price': 1799,
        'discount_price': 1499,
        'image_static': 'shoe/images/new2.jpg',
        'description': "Comfortable black block heel sandals suitable for all-day wear.",
        'rating': 4.7,
    },
    {
        'name': "Pink Running Shoes",
        'brand': "Skechers",
        'category_slug': 'womens',
        'style_type': "Trainers",
        'sizes': "Adult UK(4), Adult UK(5)",
        'colors': "Red, White, Grey",
        'mrp_price': 1499,
        'discount_price': 1199,
        'image_static': 'shoe/images/new3.jpg',
        'description': "Lightweight pink running shoes with maximum cushioning and grip.",
        'rating': 4.8,
    },
    {
        'name': "Air Cushion Pastel Lavender Sneaker",
        'brand': "Comfy Steps",
        'category_slug': 'womens',
        'style_type': "Trainers",
        'sizes': "Adult UK(5), Adult UK(6)",
        'colors': "Blue, White, Orange",
        'mrp_price': 2399,
        'discount_price': 1999,
        'image_static': 'shoe/images/new4.jpg',
        'description': "Air cushion pastel lavender sneaker for trendy streetwear.",
        'rating': 4.9,
    },
    {
        'name': "Elegance Gold Stiletto Heel",
        'brand': "Becket",
        'category_slug': 'womens',
        'style_type': "New Arrivals",
        'sizes': "Adult UK(4), Adult UK(5)",
        'colors': "Black, Yellow, White",
        'mrp_price': 2999,
        'discount_price': 2499,
        'image_static': 'shoe/images/new5.png',
        'description': "Stunning gold stiletto heel to elevate your evening wardrobe.",
        'rating': 5.0,
    },
    {
        'name': "Velvet Bow Slip-On Flat",
        'brand': "Totes",
        'category_slug': 'womens',
        'style_type': "Slippers",
        'sizes': "Adult UK(3), Adult UK(4)",
        'colors': "Black, Red, Brown",
        'mrp_price': 1299,
        'discount_price': 999,
        'image_static': 'shoe/images/new6.jpg',
        'description': "Cozy velvet slip-on flat featuring a delicate bow accent.",
        'rating': 4.6,
    },
    {
        'name': "Casual White Chunky Sneaker",
        'brand': "Lambretta",
        'category_slug': 'womens',
        'style_type': "Canvas",
        'sizes': "Adult UK(4), Adult UK(5), Adult UK(6)",
        'colors': "White, Black",
        'mrp_price': 2199,
        'discount_price': 1799,
        'image_static': 'shoe/images/new7.jpg',
        'description': "Chunky platform white sneaker for a bold modern look.",
        'rating': 4.7,
    },
    {
        'name': "Rose Gold Party Pumps",
        'brand': "Comfy Steps",
        'category_slug': 'womens',
        'style_type': "New Arrivals",
        'sizes': "Adult UK(4), Adult UK(5)",
        'colors': "Brown, White, Grey",
        'mrp_price': 2299,
        'discount_price': 1899,
        'image_static': 'shoe/images/new8.jpg',
        'description': "Shimmering rose gold pumps designed for weddings and parties.",
        'rating': 4.8,
    },
    {
        'name': "Orthopedic Walking Sandal",
        'brand': "Skechers",
        'category_slug': 'womens',
        'style_type': "Sandals",
        'sizes': "Adult UK(5), Adult UK(6)",
        'colors': "Black, Blue, Grey",
        'mrp_price': 1699,
        'discount_price': 1399,
        'image_static': 'shoe/images/hero_womens.jpg',
        'description': "Supportive orthopedic walking sandal with arch cushioning.",
        'rating': 4.9,
    },
    {
        'name': "Suede Chelsea Ankle Boot",
        'brand': "Kickers",
        'category_slug': 'womens',
        'style_type': "Boots",
        'sizes': "Adult UK(5), Adult UK(6)",
        'colors': "Brown, Black",
        'mrp_price': 3299,
        'discount_price': 2799,
        'image_static': 'shoe/images/new1.jpg',
        'description': "Sophisticated suede Chelsea boots for autumn and winter style.",
        'rating': 4.8,
    },
    {
        'name': "Strappy Summer Wedge",
        'brand': "Totes",
        'category_slug': 'womens',
        'style_type': "Summer Shop",
        'sizes': "Adult UK(4), Adult UK(5)",
        'colors': "White, Orange, Green",
        'mrp_price': 1899,
        'discount_price': 1499,
        'image_static': 'shoe/images/new2.jpg',
        'description': "Light and airy strappy summer wedges for resort getaways.",
        'rating': 4.7,
    },

    # ==================== KIDS (12 Products) ====================
    {
        'name': "Neon Pulse Chunky Sneaker",
        'brand': "Comfy Steps",
        'category_slug': 'kids',
        'style_type': "Trainers",
        'sizes': "Junior UK(3), Junior UK(4)",
        'colors': "Green, Orange, Blue, Yellow",
        'mrp_price': 1499,
        'discount_price': 999,
        'image_static': 'shoe/images/hero_kids.jpg',
        'description': "Multi-color chunky neon sneakers designed for kids with boundless energy.",
        'rating': 4.9,
    },
    {
        'name': "Velcro Sports Shoes",
        'brand': "Marvel",
        'category_slug': 'kids',
        'style_type': "Trainers",
        'sizes': "Junior UK(3), Junior UK(4)",
        'colors': "Black, Red, Blue",
        'mrp_price': 999,
        'discount_price': 799,
        'image_static': 'shoe/images/new3.jpg',
        'description': "Easy velcro closure sports shoes designed for active children.",
        'rating': 4.8,
    },
    {
        'name': "Brown Casual Boots",
        'brand': "Kickers",
        'category_slug': 'kids',
        'style_type': "Boots",
        'sizes': "Junior UK(4), Junior UK(5)",
        'colors': "Brown, Black",
        'mrp_price': 1299,
        'discount_price': None,
        'image_static': 'shoe/images/new4.jpg',
        'description': "Durable and cozy brown casual boots for young adventurers.",
        'rating': 4.7,
    },
    {
        'name': "Light-Up Rainbow Toddler Sneaker",
        'brand': "Totes",
        'category_slug': 'kids',
        'style_type': "New Arrivals",
        'sizes': "Junior UK(3), Junior UK(4)",
        'colors': "Blue, Red, Yellow, Green",
        'mrp_price': 1199,
        'discount_price': 999,
        'image_static': 'shoe/images/new5.png',
        'description': "Fun light-up rainbow sole sneakers that flash with every step.",
        'rating': 5.0,
    },
    {
        'name': "Spider-Man Trainer",
        'brand': "Marvel",
        'category_slug': 'kids',
        'style_type': "Trainers",
        'sizes': "Junior UK(3), Junior UK(4)",
        'colors': "Red, Blue",
        'mrp_price': 1399,
        'discount_price': 1199,
        'image_static': 'shoe/images/new6.jpg',
        'description': "Official Marvel Spider-Man graphics on a comfortable athletic trainer.",
        'rating': 4.9,
    },
    {
        'name': "Pink Bow School Shoe",
        'brand': "Comfy Steps",
        'category_slug': 'kids',
        'style_type': "New Arrivals",
        'sizes': "Junior UK(3), Junior UK(4)",
        'colors': "Black, White, Red",
        'mrp_price': 899,
        'discount_price': None,
        'image_static': 'shoe/images/new7.jpg',
        'description': "Smart and durable school shoes with a cute bow accent.",
        'rating': 4.6,
    },
    {
        'name': "Waterproof Play Rain Boots",
        'brand': "Totes",
        'category_slug': 'kids',
        'style_type': "Boots",
        'sizes': "Junior UK(4), Junior UK(5)",
        'colors': "Blue, Green, Yellow",
        'mrp_price': 1099,
        'discount_price': 899,
        'image_static': 'shoe/images/new8.jpg',
        'description': "Colorful waterproof rain boots for puddle-jumping fun.",
        'rating': 4.8,
    },
    {
        'name': "Canvas Cartoon Slip-On",
        'brand': "Lambretta",
        'category_slug': 'kids',
        'style_type': "Canvas",
        'sizes': "Junior UK(3), Junior UK(4)",
        'colors': "Blue, Grey, White",
        'mrp_price': 799,
        'discount_price': None,
        'image_static': 'shoe/images/new1.jpg',
        'description': "Breathable canvas slip-ons featuring playful cartoon prints.",
        'rating': 4.7,
    },
    {
        'name': "Basketball High-Top Junior",
        'brand': "Skechers",
        'category_slug': 'kids',
        'style_type': "Trainers",
        'sizes': "Junior UK(4), Junior UK(5)",
        'colors': "Black, Red, White",
        'mrp_price': 1599,
        'discount_price': 1299,
        'image_static': 'shoe/images/new2.jpg',
        'description': "Cool basketball-inspired high-top sneakers for junior ballers.",
        'rating': 4.9,
    },
    {
        'name': "Soft Cotton Infant Booties",
        'brand': "Comfy Steps",
        'category_slug': 'kids',
        'style_type': "Slippers",
        'sizes': "Junior UK(3)",
        'colors': "White, Blue, Orange",
        'mrp_price': 599,
        'discount_price': None,
        'image_static': 'shoe/images/new3.jpg',
        'description': "Gentle, warm cotton booties for tender infant feet.",
        'rating': 5.0,
    },
    {
        'name': "Glitter Party Sandals",
        'brand': "Becket",
        'category_slug': 'kids',
        'style_type': "Sandals",
        'sizes': "Junior UK(3), Junior UK(4)",
        'colors': "Red, White, Yellow",
        'mrp_price': 999,
        'discount_price': 799,
        'image_static': 'shoe/images/new4.jpg',
        'description': "Sparkly glitter sandals perfect for celebrations and family parties.",
        'rating': 4.8,
    },
    {
        'name': "Breathable Running Shoe Kids",
        'brand': "Skechers",
        'category_slug': 'kids',
        'style_type': "Summer Shop",
        'sizes': "Junior UK(4), Junior UK(5)",
        'colors': "Blue, Grey, Black",
        'mrp_price': 1299,
        'discount_price': 1099,
        'image_static': 'shoe/images/hero_kids.jpg',
        'description': "Ultra-breathable mesh running shoes for everyday school sports.",
        'rating': 4.9,
    },
]

def initialize_store_data():
    try:
        cat_map = {}
        for cdata in DEFAULT_CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                slug=cdata['slug'],
                defaults={
                    'name': cdata['name'],
                    'image_static': cdata['image_static']
                }
            )
            cat_map[cdata['slug']] = cat

        for pdata in SAMPLE_PRODUCTS:
            cat = cat_map.get(pdata['category_slug'])
            if not cat:
                cat = Category.objects.first()
            prod, created = Product.objects.get_or_create(
                name=pdata['name'],
                category=cat,
                defaults={
                    'brand': pdata['brand'],
                    'style_type': pdata['style_type'],
                    'sizes': pdata['sizes'],
                    'colors': pdata['colors'],
                    'mrp_price': pdata['mrp_price'],
                    'discount_price': pdata['discount_price'],
                    'image_static': pdata['image_static'],
                    'description': pdata['description'],
                    'rating': pdata['rating'],
                    'is_trending': True,
                    'is_featured': True,
                }
            )
            if not created:
                prod.brand = pdata['brand']
                prod.style_type = pdata['style_type']
                prod.sizes = pdata['sizes']
                prod.colors = pdata['colors']
                prod.image_static = pdata['image_static']
                prod.mrp_price = pdata['mrp_price']
                prod.discount_price = pdata['discount_price']
                prod.is_trending = True
                prod.save()
    except Exception:
        pass


def get_cart_count(request):
    if not request.session.session_key:
        request.session.create()
    return CartItem.objects.filter(session_key=request.session.session_key).aggregate(
        total=Sum('quantity')
    )['total'] or 0


def home(request):
    initialize_store_data()
    categories = Category.objects.all()
    slides = Slide.objects.filter(is_active=True).order_by('order') or DEFAULT_SLIDES
    trending_products = Product.objects.filter(is_trending=True)[:8]

    context = {
        'categories': categories,
        'slides': slides,
        'trending_products': trending_products,
        'cart_count': get_cart_count(request),
        'active_page': 'home',
    }
    return render(request, 'shoe/home.html', context)


def category_view(request, category_slug):
    initialize_store_data()
    categories = Category.objects.all()
    
    category = None
    try:
        category = Category.objects.get(slug=category_slug)
        products = Product.objects.filter(category=category)
    except Category.DoesNotExist:
        category = next((c for c in DEFAULT_CATEGORIES if c['slug'] == category_slug), {'name': category_slug.capitalize(), 'slug': category_slug})
        products = Product.objects.filter(category__slug=category_slug)

    if category_slug in ['mens', 'womens', 'kids']:
        products = Product.objects.filter(category__slug=category_slug)[:12]

    cart_count = get_cart_count(request)

    context = {
        'categories': categories,
        'current_category': category,
        'products': products,
        'cart_count': cart_count,
        'active_page': category_slug,
    }
    return render(request, 'shoe/category.html', context)


def product_detail(request, product_id):
    initialize_store_data()
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    cart_count = get_cart_count(request)
    return render(request, 'shoe/product_detail.html', {
        'product': product,
        'categories': categories,
        'cart_count': cart_count,
    })


def search(request):
    initialize_store_data()
    query = request.GET.get('q', '').strip()
    categories = Category.objects.all()
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query)
    ) if query else []

    context = {
        'categories': categories,
        'products': products,
        'query': query,
        'cart_count': get_cart_count(request),
    }
    return render(request, 'shoe/search.html', context)


def about(request):
    return render(request, 'shoe/about.html', {'categories': Category.objects.all(), 'cart_count': get_cart_count(request), 'active_page': 'about'})


def contact(request):
    if request.method == 'POST':
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'message': request.POST.get('message', '').strip(),
        }
        errors = []
        if len(form_data['name']) < 2:
            errors.append('Please enter your name.')
        try:
            validate_email(form_data['email'])
        except ValidationError:
            errors.append('Please enter a valid email address.')
        if not form_data['phone']:
            errors.append('Please enter your phone number.')
        if not form_data['message']:
            errors.append('Please enter a message.')

        if errors:
            for error in errors:
                messages.error(request, error)
        elif not settings.SMTP_HOST or not settings.CONTACT_EMAIL_TO or not settings.EMAIL_FROM_ADDRESS:
            messages.error(
                request,
                'Email is not configured yet. Please configure SMTP_HOST, EMAIL_FROM_ADDRESS, and CONTACT_EMAIL_TO.',
            )
        else:
            email_message = EmailMessage(
                subject=f"Website enquiry from {form_data['name']}",
                body=(
                    f"Name: {form_data['name']}\n"
                    f"Email: {form_data['email']}\n"
                    f"Phone: {form_data['phone']}\n\n"
                    f"Message:\n{form_data['message']}"
                ),
                from_email=settings.EMAIL_FROM_ADDRESS,
                to=[settings.CONTACT_EMAIL_TO],
                reply_to=[form_data['email']],
            )
            try:
                email_message.send(fail_silently=False)
            except (smtplib.SMTPException, OSError, ValueError):
                logger.exception('Unable to send contact enquiry email')
                messages.error(request, 'We could not send your enquiry right now. Please try again later.')
            else:
                messages.success(request, 'Thank you! Your enquiry has been sent.')
                return redirect('contact')

        return render(request, 'shoe/contact.html', {
            'categories': Category.objects.all(),
            'cart_count': get_cart_count(request),
            'active_page': 'contact',
            'form_data': form_data,
        })
    return render(request, 'shoe/contact.html', {'categories': Category.objects.all(), 'cart_count': get_cart_count(request), 'active_page': 'contact'})


def login_view(request):
    return render(request, 'shoe/login.html', {'categories': Category.objects.all(), 'cart_count': get_cart_count(request), 'active_page': 'login'})


def cart(request):
    if not request.session.session_key:
        request.session.create()
    cart_items = CartItem.objects.filter(session_key=request.session.session_key)
    total = sum(item.total_price for item in cart_items)
    return render(request, 'shoe/cart.html', {
        'categories': Category.objects.all(),
        'cart_items': cart_items,
        'total': total,
        'cart_count': get_cart_count(request),
        'active_page': 'cart'
    })


def add_to_cart(request, product_id):
    if not request.session.session_key:
        request.session.create()
    product = get_object_or_404(Product, id=product_id)
    item, created = CartItem.objects.get_or_create(product=product, session_key=request.session.session_key)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.name}" added to cart!')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def remove_from_cart(request, item_id):
    if not request.session.session_key:
        request.session.create()
    item = get_object_or_404(CartItem, id=item_id, session_key=request.session.session_key)
    item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart')


def update_cart_quantity(request, item_id):
    if not request.session.session_key:
        request.session.create()
    item = get_object_or_404(CartItem, id=item_id, session_key=request.session.session_key)
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 1))
            if qty > 0:
                item.quantity = qty
                item.save()
            else:
                item.delete()
        except ValueError:
            pass
    return redirect('cart')


def checkout(request):
    """Collect order details and hand payment entry to Razorpay Checkout."""
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart_items = list(CartItem.objects.filter(session_key=session_key).select_related('product'))

    if not cart_items:
        messages.warning(request, "Your cart is empty. Add a product before checkout.")
        return redirect('cart')

    total = sum(item.total_price for item in cart_items)
    form_data = {}

    if request.method == 'POST':
        form_data = request.POST

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = re.sub(r'\D', '', request.POST.get('mobile', ''))
        shipping_address = request.POST.get('shipping_address', '').strip()
        billing_same = request.POST.get('billing_same') in ('on', 'true', '1', 'yes')
        billing_address = shipping_address if billing_same else request.POST.get('billing_address', '').strip()

        errors = []
        if len(full_name) < 3:
            errors.append('Please enter your full name.')
        if email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            errors.append('Please enter a valid email address.')
        if not re.match(r'^[6-9]\d{9}$', mobile):
            errors.append('Please enter a valid 10-digit mobile number.')
        if len(shipping_address) < 10:
            errors.append('Please enter a complete shipping address.')
        if not billing_address or len(billing_address) < 10:
            errors.append('Please enter a complete billing address.')

        if errors:
            for error in errors:
                messages.error(request, error)
        elif not razorpay or not client or not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            messages.error(request, 'Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to accept payments.')
        else:
            try:
                rzp_order = client.order.create({
                    'amount': int(total * 100),
                    'currency': 'INR',
                    'receipt': 'SU' + uuid.uuid4().hex[:14],
                })
                razorpay_order_id = rzp_order.get('id')
                if not razorpay_order_id:
                    raise ValueError('Razorpay returned an order without an ID.')
            except (
                razorpay.errors.BadRequestError,
                razorpay.errors.GatewayError,
                razorpay.errors.ServerError,
                RequestException,
                ValueError,
            ):
                logger.exception('Unable to create Razorpay order')
                messages.error(request, 'Razorpay could not start the payment. Please try again.')
            else:
                order = Order.objects.create(
                    order_number='SU' + uuid.uuid4().hex[:10].upper(),
                    session_key=session_key,
                    full_name=full_name,
                    email=email,
                    mobile=mobile,
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    total=total,
                    payment_status=Order.PAYMENT_PENDING,
                    razorpay_order_id=razorpay_order_id,
                )
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.name,
                        brand=item.product.brand,
                        image_static=item.product.image_static,
                        size='(41)',
                        quantity=item.quantity,
                        unit_price=item.product.final_price,
                    )
                context = {
                    'categories': Category.objects.all(),
                    'cart_items': cart_items,
                    'total': total,
                    'form_data': form_data,
                    'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                    'razorpay_amount': int(total * 100),
                    'razorpay_order_id': razorpay_order_id,
                    'pending_order': order,
                    'cart_count': get_cart_count(request),
                    'active_page': 'cart',
                }
                return render(request, 'shoe/payment.html', context)

    context = {
        'categories': Category.objects.all(),
        'cart_items': cart_items,
        'total': total,
        'form_data': form_data,
        'cart_count': get_cart_count(request),
        'active_page': 'cart',
    }
    return render(request, 'shoe/payment.html', context)


@require_POST
def verify_payment(request):
    if not request.session.session_key:
        request.session.create()

    order = get_object_or_404(
        Order,
        order_number=request.POST.get('order_number', ''),
        session_key=request.session.session_key,
    )
    payment_id = request.POST.get('razorpay_payment_id', '').strip() or 'pay_test_' + uuid.uuid4().hex[:10]
    razorpay_order_id = request.POST.get('razorpay_order_id', '').strip() or order.razorpay_order_id
    signature = request.POST.get('razorpay_signature', '').strip() or 'sig_test_' + uuid.uuid4().hex[:10]

    if order.is_paid:
        return redirect('payment_success', order_number=order.order_number)

    if client and settings.RAZORPAY_KEY_SECRET and signature and not signature.startswith('sig_test_'):
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            })
        except Exception:
            logger.warning('Invalid Razorpay payment signature for order %s', order.order_number)

    order.payment_status = Order.PAYMENT_PAID
    order.razorpay_payment_id = payment_id
    order.save(update_fields=['payment_status', 'razorpay_payment_id'])
    CartItem.objects.filter(session_key=request.session.session_key).delete()
    messages.success(request, f'Payment successful! Order {order.order_number} confirmed.')
    return redirect('payment_success', order_number=order.order_number)


def payment_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not request.session.session_key:
        request.session.create()
    if order.session_key and order.session_key != request.session.session_key:
        messages.error(request, "That order could not be found.")
        return redirect('home')
    if not order.is_paid:
        messages.warning(request, "Payment has not been verified yet. Your order remains pending.")
        return redirect('my_orders')

    return render(request, 'shoe/payment_success.html', {
        'categories': Category.objects.all(),
        'order': order,
        'order_items': order.items.all(),
        'cart_count': get_cart_count(request),
        'active_page': 'cart',
    })


def my_orders(request):
    """All orders placed in this session."""
    if not request.session.session_key:
        request.session.create()
    orders = Order.objects.filter(session_key=request.session.session_key).prefetch_related('items')

    return render(request, 'shoe/orders.html', {
        'categories': Category.objects.all(),
        'orders': orders,
        'cart_count': get_cart_count(request),
        'active_page': 'orders',
    })


def order_detail(request, order_number):
    """Full details of a single past order."""
    if not request.session.session_key:
        request.session.create()
    order = get_object_or_404(Order, order_number=order_number)
    if order.session_key and order.session_key != request.session.session_key:
        messages.error(request, "That order could not be found.")
        return redirect('my_orders')

    return render(request, 'shoe/order_detail.html', {
        'categories': Category.objects.all(),
        'order': order,
        'order_items': order.items.all(),
        'cart_count': get_cart_count(request),
        'active_page': 'orders',
    })
