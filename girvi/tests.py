import unittest
from django.urls import reverse
from django.test import Client
from .models import License, Loan, Release
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


def create_license(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["type"] = "type"
    defaults["shopname"] = "shopname"
    defaults["address"] = "address"
    defaults["phonenumber"] = "phonenumber"
    defaults["propreitor"] = "propreitor"
    defaults.update(**kwargs)
    return License.objects.create(**defaults)


def create_loan(**kwargs):
    defaults = {}
    defaults["loanid"] = "loanid"
    defaults["itemtype"] = "itemtype"
    defaults["itemdesc"] = "itemdesc"
    defaults["itemweight"] = "itemweight"
    defaults["itemvalue"] = "itemvalue"
    defaults["loanamount"] = "loanamount"
    defaults["interestrate"] = "interestrate"
    defaults["interest"] = "interest"
    defaults.update(**kwargs)
    if "license" not in defaults:
        defaults["license"] = create_django_contrib_auth_models_user()
    if "customer" not in defaults:
        defaults["customer"] = create_django_contrib_auth_models_user()
    return Loan.objects.create(**defaults)


def create_release(**kwargs):
    defaults = {}
    defaults["releaseid"] = "releaseid"
    defaults["interestpaid"] = "interestpaid"
    defaults.update(**kwargs)
    if "loan" not in defaults:
        defaults["loan"] = create_loan()
    return Release.objects.create(**defaults)


class LicenseViewTest(unittest.TestCase):
    '''
    Tests for License
    '''
    def setUp(self):
        self.client = Client()

    def test_list_license(self):
        url = reverse('girvi_license_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_license(self):
        url = reverse('girvi_license_create')
        data = {
            "name": "name",
            "type": "type",
            "shopname": "shopname",
            "address": "address",
            "phonenumber": "phonenumber",
            "propreitor": "propreitor",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_license(self):
        license = create_license()
        url = reverse('girvi_license_detail', args=[license.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_license(self):
        license = create_license()
        data = {
            "name": "name",
            "type": "type",
            "shopname": "shopname",
            "address": "address",
            "phonenumber": "phonenumber",
            "propreitor": "propreitor",
        }
        url = reverse('girvi_license_update', args=[license.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class LoanViewTest(unittest.TestCase):
    '''
    Tests for Loan
    '''
    def setUp(self):
        self.client = Client()

    def test_list_loan(self):
        url = reverse('girvi_loan_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_loan(self):
        url = reverse('girvi_loan_create')
        data = {
            "loanid": "loanid",
            "itemtype": "itemtype",
            "itemdesc": "itemdesc",
            "itemweight": "itemweight",
            "itemvalue": "itemvalue",
            "loanamount": "loanamount",
            "interestrate": "interestrate",
            "interest": "interest",
            "license": create_django_contrib_auth_models_user().pk,
            "customer": create_django_contrib_auth_models_user().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_loan(self):
        loan = create_loan()
        url = reverse('girvi_loan_detail', args=[loan.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_loan(self):
        loan = create_loan()
        data = {
            "loanid": "loanid",
            "itemtype": "itemtype",
            "itemdesc": "itemdesc",
            "itemweight": "itemweight",
            "itemvalue": "itemvalue",
            "loanamount": "loanamount",
            "interestrate": "interestrate",
            "interest": "interest",
            "license": create_django_contrib_auth_models_user().pk,
            "customer": create_django_contrib_auth_models_user().pk,
        }
        url = reverse('girvi_loan_update', args=[loan.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class ReleaseViewTest(unittest.TestCase):
    '''
    Tests for Release
    '''
    def setUp(self):
        self.client = Client()

    def test_list_release(self):
        url = reverse('girvi_release_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_release(self):
        url = reverse('girvi_release_create')
        data = {
            "releaseid": "releaseid",
            "interestpaid": "interestpaid",
            "loan": create_loan().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_release(self):
        release = create_release()
        url = reverse('girvi_release_detail', args=[release.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_release(self):
        release = create_release()
        data = {
            "releaseid": "releaseid",
            "interestpaid": "interestpaid",
            "loan": create_loan().pk,
        }
        url = reverse('girvi_release_update', args=[release.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


