import unittest
from django.urls import reverse
from django.test import Client
from .models import Contact, Chit, Collection, Allotment
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


def create_contact(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["phoneno"] = "phoneno"
    defaults.update(**kwargs)
    return Contact.objects.create(**defaults)


def create_chit(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["type"] = "type"
    defaults["amount"] = "amount"
    defaults["commission"] = "commission"
    defaults["member_limit"] = "member_limit"
    defaults["date_to_allot"] = "date_to_allot"
    defaults.update(**kwargs)
    if "owner" not in defaults:
        defaults["owner"] = create_contact()
    if "members" not in defaults:
        defaults["members"] = create_contact()
    return Chit.objects.create(**defaults)


def create_collection(**kwargs):
    defaults = {}
    defaults["amount"] = "amount"
    defaults.update(**kwargs)
    if "chit" not in defaults:
        defaults["chit"] = create_chit()
    if "member" not in defaults:
        defaults["member"] = create_contact()
    return Collection.objects.create(**defaults)


def create_allotment(**kwargs):
    defaults = {}
    defaults["amount"] = "amount"
    defaults.update(**kwargs)
    if "chit" not in defaults:
        defaults["chit"] = create_chit()
    if "to_member" not in defaults:
        defaults["to_member"] = create_contact()
    return Allotment.objects.create(**defaults)


class ContactViewTest(unittest.TestCase):
    '''
    Tests for Contact
    '''
    def setUp(self):
        self.client = Client()

    def test_list_contact(self):
        url = reverse('Chitfund_contact_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_contact(self):
        url = reverse('Chitfund_contact_create')
        data = {
            "name": "name",
            "phoneno": "phoneno",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_contact(self):
        contact = create_contact()
        url = reverse('Chitfund_contact_detail', args=[contact.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_contact(self):
        contact = create_contact()
        data = {
            "name": "name",
            "phoneno": "phoneno",
        }
        url = reverse('Chitfund_contact_update', args=[contact.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class ChitViewTest(unittest.TestCase):
    '''
    Tests for Chit
    '''
    def setUp(self):
        self.client = Client()

    def test_list_chit(self):
        url = reverse('Chitfund_chit_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_chit(self):
        url = reverse('Chitfund_chit_create')
        data = {
            "name": "name",
            "type": "type",
            "amount": "amount",
            "commission": "commission",
            "member_limit": "member_limit",
            "date_to_allot": "date_to_allot",
            "owner": create_contact().pk,
            "members": create_contact().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_chit(self):
        chit = create_chit()
        url = reverse('Chitfund_chit_detail', args=[chit.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_chit(self):
        chit = create_chit()
        data = {
            "name": "name",
            "type": "type",
            "amount": "amount",
            "commission": "commission",
            "member_limit": "member_limit",
            "date_to_allot": "date_to_allot",
            "owner": create_contact().pk,
            "members": create_contact().pk,
        }
        url = reverse('Chitfund_chit_update', args=[chit.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class CollectionViewTest(unittest.TestCase):
    '''
    Tests for Collection
    '''
    def setUp(self):
        self.client = Client()

    def test_list_collection(self):
        url = reverse('Chitfund_collection_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_collection(self):
        url = reverse('Chitfund_collection_create')
        data = {
            "amount": "amount",
            "chit": create_chit().pk,
            "member": create_contact().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_collection(self):
        collection = create_collection()
        url = reverse('Chitfund_collection_detail', args=[collection.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_collection(self):
        collection = create_collection()
        data = {
            "amount": "amount",
            "chit": create_chit().pk,
            "member": create_contact().pk,
        }
        url = reverse('Chitfund_collection_update', args=[collection.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class AllotmentViewTest(unittest.TestCase):
    '''
    Tests for Allotment
    '''
    def setUp(self):
        self.client = Client()

    def test_list_allotment(self):
        url = reverse('Chitfund_allotment_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_allotment(self):
        url = reverse('Chitfund_allotment_create')
        data = {
            "amount": "amount",
            "chit": create_chit().pk,
            "to_member": create_contact().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_allotment(self):
        allotment = create_allotment()
        url = reverse('Chitfund_allotment_detail', args=[allotment.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_allotment(self):
        allotment = create_allotment()
        data = {
            "amount": "amount",
            "chit": create_chit().pk,
            "to_member": create_contact().pk,
        }
        url = reverse('Chitfund_allotment_update', args=[allotment.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


