from django.urls import reverse
from .models import Customer, Contact, Address, Proof, CustomerRelationship
from django.test import TestCase

class CustomerModelTest(TestCase):
    def test_create_customer(self):
        customer = Customer.objects.create(
            name='John Doe',
            phonenumber='1234567890',
            address='123 Main St',
            type='Individual',
            relatedas='Friend',
            relatedto='Jane Doe'
        )
        self.assertEqual(customer.name, 'John Doe')
        self.assertEqual(customer.phonenumber, '1234567890')
        self.assertEqual(customer.address, '123 Main St')
        self.assertEqual(customer.type, 'Individual')
        self.assertEqual(customer.relatedas, 'Friend')
        self.assertEqual(customer.relatedto, 'Jane Doe')

class ContactModelTest(TestCase):
    def test_create_contact(self):
        contact = Contact.objects.create(
            name='John Doe',
            email='john@example.com',
            phone='1234567890'
        )
        self.assertEqual(contact.name, 'John Doe')
        self.assertEqual(contact.email, 'john@example.com')
        self.assertEqual(contact.phone, '1234567890')

class AddressModelTest(TestCase):
    def test_create_address(self):
        address = Address.objects.create(
            street='123 Main St',
            city='New York',
            state='NY',
            zip_code='10001'
        )
        self.assertEqual(address.street, '123 Main St')
        self.assertEqual(address.city, 'New York')
        self.assertEqual(address.state, 'NY')
        self.assertEqual(address.zip_code, '10001')

class ProofModelTest(TestCase):
    def test_create_proof(self):
        proof = Proof.objects.create(
            type='ID',
            number='1234567890'
        )
        self.assertEqual(proof.type, 'ID')
        self.assertEqual(proof.number, '1234567890')

class CustomerRelationshipModelTest(TestCase):
    def test_create_customer_relationship(self):
        customer = Customer.objects.create(
            name='John Doe',
            phonenumber='1234567890',
            address='123 Main St',
            type='Individual',
            relatedas='Friend',
            relatedto='Jane Doe'
        )
        relationship = CustomerRelationship.objects.create(
            customer=customer,
            relationship='Friend',
            related_customer='Jane Doe'
        )
        self.assertEqual(relationship.customer, customer)
        self.assertEqual(relationship.relationship, 'Friend')
        self.assertEqual(relationship.related_customer, 'Jane Doe')



class CustomerViewTest(TestCase):
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
        customer = Customer.objects.create(
            name='John Doe',
            phonenumber='1234567890',
            address='123 Main St',
            type='Individual',
            relatedas='Friend',
            relatedto='Jane Doe'
        )
        url = reverse('contact_customer_detail', args=[customer.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_customer(self):
        customer = Customer.objects.create(
            name='John Doe',
            phonenumber='1234567890',
            address='123 Main St',
            type='Individual',
            relatedas='Friend',
            relatedto='Jane Doe'
        )
        data = {
            "name": "name",
            "phonenumber": "phonenumber",
            "Address": "Address",
            "type": "type",
            "relatedas": "relatedas",
            "relatedto": "relatedto",
        }
        url = reverse('contact_customer_update', args=[customer.slug])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)