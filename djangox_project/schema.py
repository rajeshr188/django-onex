import graphene
# import graphql_jwt
import contact.schema

class Query(contact.schema.Query,graphene.ObjectType):
    pass

class Mutation(contact.schema.Mutation,graphene.ObjectType):
    pass
    # token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    # verify_token = graphql_jwt.Verify.Field()
    # refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query = Query,mutation= Mutation
)