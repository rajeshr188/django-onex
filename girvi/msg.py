from environ import Env
from twilio.rest import Client

env = Env()


def notify_msg(number, content):
    client = Client(env("TWILIO_ACCOUNT_SID"), env("TWILIO_AUTH_TOKEN"))

    message = client.messages.create(
        body=content, from_=env("TWILIO_NUMBER"), to=number
    )

    return message.sid
