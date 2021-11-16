from psycopg2.extras import register_composite
from psycopg2.extensions import register_adapter, adapt, AsIs
from django.db import models, connection
from moneyed import Money

MoneyValue = register_composite(
    'money_value',
    connection.cursor().cursor,
    globally=True
).type


def moneyvalue_adapter(value):
    return AsIs("(%s,%s)::money_value" % (
        adapt(value.amount),
        adapt(value.currency.code)))


register_adapter(Money, moneyvalue_adapter)


class MoneyValueField(models.Field):
    description = "wrapper for money_value composite type in postgres"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return Money(value.amount, value.currency)

    def to_python(self, value):
        if isinstance(value, Money):
            return value
        if value is None:
            return value
        return Money(value.amount, value.currency.code)

    def get_prep_value(self, value):
        # in admin input box we enter 10 USD,20 INR,30 AUD

        if isinstance(value, Money):
            return value
        else:
            amount, currency = value.split()
            return Money(amount, currency)

    def db_type(self, connection):
        return 'money_value'
