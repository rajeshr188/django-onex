import unittest
from django.urls import reverse
from django.test import Client
from .models import Invoice, InvoiceItem, Payment
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType


def create_django_contrib_auth_models_user(**kwargs):
    defaults = {}
    defaults["username"] = "username"
    defaults["email"] = "username@tempurl.com"
    defaults.update(**kwargs)
    return User.objects.create(**defaults)


def create_django_contrib_auth_models_group(**kwargs):
    defaults = {}
    defaults["name"] = "group"
    defaults.update(**kwargs)
    return Group.objects.create(**defaults)


def create_django_contrib_contenttypes_models_contenttype(**kwargs):
    defaults = {}
    defaults.update(**kwargs)
    return ContentType.objects.create(**defaults)


def create_invoice(**kwargs):
    defaults = {}
    defaults["rate"] = "rate"
    defaults["balancetype"] = "balancetype"
    defaults["paymenttype"] = "paymenttype"
    defaults["balance"] = "balance"
    defaults["status"] = "status"
    defaults.update(**kwargs)
    if "supplier" not in defaults:
        defaults["supplier"] = create_django_contrib_auth_models_user()
    return Invoice.objects.create(**defaults)


def create_invoiceitem(**kwargs):
    defaults = {}
    defaults["weight"] = "weight"
    defaults["touch"] = "touch"
    defaults["total"] = "total"
    defaults["is_return"] = "is_return"
    defaults["quantity"] = "quantity"
    defaults.update(**kwargs)
    if "product" not in defaults:
        defaults["product"] = create_django_contrib_auth_models_user()
    if "invoice" not in defaults:
        defaults["invoice"] = create_invoice()
    return InvoiceItem.objects.create(**defaults)


def create_payment(**kwargs):
    defaults = {}
    defaults["type"] = "type"
    defaults["total"] = "total"
    defaults["description"] = "description"
    defaults.update(**kwargs)
    if "supplier" not in defaults:
        defaults["supplier"] = create_django_contrib_auth_models_user()
    return Payment.objects.create(**defaults)


class InvoiceViewTest(unittest.TestCase):
    '''
    Tests for Invoice
    '''
    def setUp(self):
        self.client = Client()

    def test_list_invoice(self):
        url = reverse('purchase_invoice_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_invoice(self):
        url = reverse('purchase_invoice_create')
        data = {
            "rate": "rate",
            "balancetype": "balancetype",
            "paymenttype": "paymenttype",
            "balance": "balance",
            "status": "status",
            "supplier": create_django_contrib_auth_models_user().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_invoice(self):
        invoice = create_invoice()
        url = reverse('purchase_invoice_detail', args=[invoice.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_invoice(self):
        invoice = create_invoice()
        data = {
            "rate": "rate",
            "balancetype": "balancetype",
            "paymenttype": "paymenttype",
            "balance": "balance",
            "status": "status",
            "supplier": create_django_contrib_auth_models_user().pk,
        }
        url = reverse('purchase_invoice_update', args=[invoice.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class InvoiceItemViewTest(unittest.TestCase):
    '''
    Tests for InvoiceItem
    '''
    def setUp(self):
        self.client = Client()

    def test_list_invoiceitem(self):
        url = reverse('purchase_invoiceitem_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_invoiceitem(self):
        url = reverse('purchase_invoiceitem_create')
        data = {
            "weight": "weight",
            "touch": "touch",
            "total": "total",
            "is_return": "is_return",
            "quantity": "quantity",
            "product": create_django_contrib_auth_models_user().pk,
            "invoice": create_invoice().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_invoiceitem(self):
        invoiceitem = create_invoiceitem()
        url = reverse('purchase_invoiceitem_detail', args=[invoiceitem.pk,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_invoiceitem(self):
        invoiceitem = create_invoiceitem()
        data = {
            "weight": "weight",
            "touch": "touch",
            "total": "total",
            "is_return": "is_return",
            "quantity": "quantity",
            "product": create_django_contrib_auth_models_user().pk,
            "invoice": create_invoice().pk,
        }
        url = reverse('purchase_invoiceitem_update', args=[invoiceitem.pk,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class PaymentViewTest(unittest.TestCase):
    '''
    Tests for Payment
    '''
    def setUp(self):
        self.client = Client()

    def test_list_payment(self):
        url = reverse('purchase_payment_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_payment(self):
        url = reverse('purchase_payment_create')
        data = {
            "type": "type",
            "total": "total",
            "description": "description",
            "supplier": create_django_contrib_auth_models_user().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_payment(self):
        payment = create_payment()
        url = reverse('purchase_payment_detail', args=[payment.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_payment(self):
        payment = create_payment()
        data = {
            "type": "type",
            "total": "total",
            "description": "description",
            "supplier": create_django_contrib_auth_models_user().pk,
        }
        url = reverse('purchase_payment_update', args=[payment.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


