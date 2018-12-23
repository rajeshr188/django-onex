from twilio.rest import Client


# Your Account Sid and Auth Token from twilio.com/console
account_sid = 'AC4d5e1f0e0bc4bb0c77e2e6f5f4912420'
auth_token = 'your_auth_token'
client = Client(account_sid, auth_token)

message = client.messages.create(
                              body='Hello there!',
                              from_='whatsapp:+14155238886',
                              to='whatsapp:+15005550006'
                          )

print(message.sid)
