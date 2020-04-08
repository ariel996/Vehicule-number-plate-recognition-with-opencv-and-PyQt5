import nexmo

# let's construct a client object with our api_key and secret key
client = nexmo.Client(key='a3cc9732',secret='48e75c68e84f52c2')

# let's send a text message
response = client.send_message(
    {'from': 'VNPR',
     'to': '699501442',
     'text': 'HelloWorld'
     })
response = response['messages'][0]
if response['status'] == '0':
    print('Sent message', response['message-id'])

    print('Remaining balance is', response['remaining-balance'])
else:
    print('Error:', response['error-text'])