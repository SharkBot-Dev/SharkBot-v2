import requests

text = input('? ')

j = requests.post('http://localhost:6200/', json={'text': text})

print(j.json())