import graphene

import contact.schema

class Query(contact.schema.Query,graphene.ObjectType):
    pass

class Mutation(contact.schema.Mutation,graphene.ObjectType):
    pass

schema = graphene.Schema(query = Query,mutation= Mutation)