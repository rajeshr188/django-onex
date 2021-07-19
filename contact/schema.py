import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        filter_fields = ['name','relatedas','phonenumber','area']
        interfaces = (relay.Node,)

class Query(graphene.ObjectType):
    customers = DjangoFilterConnectionField(CustomerType)

    # def resolve_customers(self,info,**kwargs):
    #     return Customer.objects.all()

class CreateCustomer(graphene.Mutation):
    id = graphene.Int()
    name = graphene.String()

    class Arguments:
        name = graphene.String()
        relatedas = graphene.String()
        relatedto = graphene.String()
        type = graphene.String()
        address = graphene.String()
        phonenumber = graphene.String()
        area = graphene.String()
        rank = graphene.Int()
    
    def mutate(self,info,name,relatedas,relatedto,type,address,phonenumber,area,rank):
        c = Customer(name = name,
                    relatedas=relatedas,relatedto = relatedto,
                    type = type,address = address,area = area,
                    phonenumber = phonenumber,rank=rank)
        c.save()
        return CreateCustomer(id = c.id,name = c.name)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()