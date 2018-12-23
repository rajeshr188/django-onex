import unittest
from django.urls import reverse
from django.test import Client
from .models import Customer, Supplier
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


def create_customer(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["phonenumber"] = "phonenumber"
    defaults["Address"] = "Address"
    defaults["type"] = "type"
    defaults["relatedas"] = "relatedas"
    defaults["relatedto"] = "relatedto"
    defaults.update(**kwargs)
    return Customer.objects.create(**defaults)


def create_supplier(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["organisation"] = "organisation"
    defaults["phonenumber"] = "phonenumber"
    defaults["initial"] = "initial"
    defaults.update(**kwargs)
    return Supplier.objects.create(**defaults)


class CustomerViewTest(unittest.TestCase):
    '''
    Tests for Customer
    '''
    def setUp(self):
        self.client = Client()

    def test_list_customer(self):
        url = reverse('contact_customer_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_customer(self):
        url = reverse('contact_customer_create')
        data = {
            "name": "name",
            "phonenumber": "phonenumber",
            "Address": "Address",
            "type": "type",
            "relatedas": "relatedas",
            "relatedto": "relatedto",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_customer(self):
        customer = create_customer()
        url = reverse('contact_customer_detail', args=[customer.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_customer(self):
        customer = create_customer()
        data = {
            "name": "name",
            "phonenumber": "phonenumber",
            "Address": "Address",
            "type": "type",
            "relatedas": "relatedas",
            "relatedto": "relatedto",
        }
        url = reverse('contact_customer_update', args=[customer.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class SupplierViewTest(unittest.TestCase):
    '''
    Tests for Supplier
    '''
    def setUp(self):
        self.client = Client()

    def test_list_supplier(self):
        url = reverse('contact_supplier_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_supplier(self):
        url = reverse('contact_supplier_create')
        data = {
            "name": "name",
            "organisation": "organisation",
            "phonenumber": "phonenumber",
            "initial": "initial",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_supplier(self):
        supplier = create_supplier()
        url = reverse('contact_supplier_detail', args=[supplier.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_supplier(self):
        supplier = create_supplier()
        data = {
            "name": "name",
            "organisation": "organisation",
            "phonenumber": "phonenumber",
            "initial": "initial",
        }
        url = reverse('contact_supplier_update', args=[supplier.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


