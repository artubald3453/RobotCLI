"""Simple example client showing how an AI integration could register and request the schema.

Run with:

    pip install requests
    python ai_client.py

This is only an example and not required for server operation.
"""
import requests

BASE = 'http://127.0.0.1:8000'

def main():
    print('Registering AI settings...')
    r = requests.post(BASE + '/api/ai/register', json={'api_key': 'testkey', 'model': 'test-model', 'enabled': True})
    print('register:', r.status_code, r.json())

    print('\nFetching schema...')
    r = requests.get(BASE + '/api/ai/schema')
    print('schema:', r.status_code)
    print(r.text)

    print('\nRequesting status via AI execute (with key)')
    r = requests.post(BASE + '/api/ai/execute', json={'api_key': 'testkey', 'command': {'action': 'status'}})
    print('execute:', r.status_code, r.text)

if __name__ == '__main__':
    main()
