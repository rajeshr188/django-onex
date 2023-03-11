# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = "AC3cebde817b5b745c30525cce09f93cbd"

auth_token = "eaa9f98ea46b528e76accd0502cbcfb4"

client = Client(account_sid, auth_token)

message = client.messages.create(
    body="Hi there HANUMANJI",
    #   from_='+15017122661',
    from_="+15673132764",
    #   to='+15558675310'
    to="+918438982536",
)


# message = client.messages.create(
#     from_="whatsapp:+14155238886",
#     body="Your appointment is coming up on July 21 at 3PM",
#     to="whatsapp:+919489481436",
# )
def send_msg(to, message):
    account_sid = "AC3cebde817b5b745c30525cce09f93cbd"

    auth_token = "eaa9f98ea46b528e76accd0502cbcfb4"

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body="Hi there HANUMANJI",
        #   from_='+15017122661',
        from_="+15673132764",
        #   to='+15558675310'
        to="+918438982536",
    )
    return msg.sid
