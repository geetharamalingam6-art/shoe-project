from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

import razorpay
from .models import CartItem, Category, Order, Product


@override_settings(RAZORPAY_KEY_ID='rzp_test_key', RAZORPAY_KEY_SECRET='test_secret')
class RazorpayCheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Test Shoes')
        product = Product.objects.create(
            category=category,
            name='Test Sneaker',
            mrp_price=1200,
            image_static='shoe/images/men1.png',
        )
        session = self.client.session
        session.save()
        self.session_key = session.session_key
        CartItem.objects.create(product=product, quantity=1, session_key=self.session_key)

    def start_checkout(self, razorpay_client):
        razorpay_client.order.create.return_value = {'id': 'order_test_123'}
        response = self.client.post(reverse('checkout'), {
            'full_name': 'Test Customer',
            'email': 'customer@example.com',
            'mobile': '9876543210',
            'shipping_address': '123 Example Street, Test City',
            'billing_same': 'on',
        })
        self.assertTemplateUsed(response, 'shoe/payment.html')
        return response, Order.objects.get(session_key=self.session_key)

    def test_checkout_uses_razorpay_modal_and_keeps_order_pending(self):
        gateway = Mock()
        with patch('shoe.views.client', gateway):
            response, order = self.start_checkout(gateway)

        self.assertEqual(order.payment_status, Order.PAYMENT_PENDING)
        self.assertEqual(order.razorpay_order_id, 'order_test_123')
        self.assertContains(response, 'checkout.razorpay.com/v1/checkout.js')
        self.assertContains(response, 'remember_customer: false')
        self.assertNotContains(response, 'name="card_number"')
        self.assertNotContains(response, 'name="cvv"')
        pending_response = self.client.get(reverse('payment_success', args=[order.order_number]))
        self.assertRedirects(pending_response, reverse('my_orders'))
        gateway.order.create.assert_called_once()
        request_data = gateway.order.create.call_args.args[0]
        self.assertEqual(request_data['amount'], 120000)
        self.assertEqual(request_data['currency'], 'INR')
        self.assertTrue(request_data['receipt'].startswith('SU'))

    def test_verified_payment_marks_order_paid_and_clears_cart(self):
        gateway = Mock()
        with patch('shoe.views.client', gateway):
            _, order = self.start_checkout(gateway)
            response = self.client.post(reverse('verify_payment'), {
                'order_number': order.order_number,
                'razorpay_order_id': 'order_test_123',
                'razorpay_payment_id': 'pay_test_123',
                'razorpay_signature': 'valid_signature',
            })

        order.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)
        self.assertEqual(order.razorpay_payment_id, 'pay_test_123')
        self.assertFalse(CartItem.objects.filter(session_key=self.session_key).exists())
        gateway.utility.verify_payment_signature.assert_called_once()
        invoice_response = self.client.get(reverse('order_detail', args=[order.order_number]))
        self.assertContains(invoice_response, f'INV-{order.order_number}')
        self.assertContains(invoice_response, 'Print / Save as PDF')
        self.assertContains(invoice_response, 'pay_test_123')

    def test_invalid_signature_does_not_mark_order_paid_or_clear_cart(self):
        gateway = Mock()
        gateway.utility.verify_payment_signature.side_effect = razorpay.errors.SignatureVerificationError(
            'invalid signature'
        )
        with patch('shoe.views.client', gateway):
            _, order = self.start_checkout(gateway)
            self.client.post(reverse('verify_payment'), {
                'order_number': order.order_number,
                'razorpay_order_id': 'order_test_123',
                'razorpay_payment_id': 'pay_test_123',
                'razorpay_signature': 'invalid_signature',
            })

        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PAYMENT_PENDING)
        self.assertFalse(order.razorpay_payment_id)
        self.assertTrue(CartItem.objects.filter(session_key=self.session_key).exists())


@override_settings(
    SMTP_HOST='smtp.example.com',
    EMAIL_FROM_ADDRESS='store@example.com',
    CONTACT_EMAIL_TO='support@example.com',
)
class ContactEmailTests(TestCase):
    def test_valid_enquiry_is_emailed_and_reply_goes_to_customer(self):
        with patch('shoe.views.EmailMessage') as email_class:
            email_class.return_value.send.return_value = 1
            response = self.client.post(reverse('contact'), {
                'name': 'Jane Customer',
                'email': 'jane@example.com',
                'phone': '9876543210',
                'message': 'I have a question about my order.',
            })

        self.assertRedirects(response, reverse('contact'))
        email_class.assert_called_once()
        email_data = email_class.call_args.kwargs
        self.assertEqual(email_data['to'], ['support@example.com'])
        self.assertEqual(email_data['reply_to'], ['jane@example.com'])
        self.assertIn('I have a question about my order.', email_data['body'])
        email_class.return_value.send.assert_called_once_with(fail_silently=False)

    def test_missing_smtp_configuration_does_not_claim_enquiry_was_sent(self):
        with override_settings(SMTP_HOST='', CONTACT_EMAIL_TO=''):
            response = self.client.post(reverse('contact'), {
                'name': 'Jane Customer',
                'email': 'jane@example.com',
                'phone': '9876543210',
                'message': 'I have a question about my order.',
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email is not configured yet')
        self.assertNotContains(response, 'Your enquiry has been sent')


class CartBadgeTests(TestCase):
    def setUp(self):
        session = self.client.session
        session.save()
        self.session_key = session.session_key

    def test_empty_cart_badge_is_zero(self):
        response = self.client.get(reverse('cart'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cart_count'], 0)
        self.assertContains(response, 'cart-badge-empty">0</span>')

    def test_cart_badge_counts_cart_lines(self):
        category = Category.objects.create(name='Badge Test Shoes')
        product = Product.objects.create(
            category=category,
            name='Badge Test Sneaker',
            mrp_price=900,
        )
        CartItem.objects.create(
            product=product,
            quantity=3,
            session_key=self.session_key,
        )

        response = self.client.get(reverse('cart'))

        self.assertEqual(response.context['cart_count'], 3)
        self.assertContains(response, 'class="cart-badge">3</span>')
