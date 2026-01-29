"""Simple integration tests for RobotCLI REST API.

Run with:

    pip3 install requests
    python3 tests/integration_test.py

Set ROBOTCLI_URL env var to point at the server, e.g. http://127.0.0.1:8000
"""

import os
import time
import requests

BASE = os.environ.get('ROBOTCLI_URL', 'http://127.0.0.1:8000')

def post_json(path, payload):
    url = BASE + path
    r = requests.post(url, json=payload)
    print(path, r.status_code, r.text)
    r.raise_for_status()
    return r.json()

def get_json(path):
    url = BASE + path
    r = requests.get(url)
    print(path, r.status_code)
    r.raise_for_status()
    return r.json()


def main():
    try:
        # Map config_spot27 -> 26
        post_json('/api/config/gpio-pins', {'config_spot': 'config_spot27', 'pin_num': 26})

        # Add alias with auto_off=False
        post_json('/api/config/aliases', {'name': 'test_motor', 'config_spot': 'config_spot27', 'auto_off': False})

        # Activate (should remain ON since auto_off=False)
        post_json('/api/activate', {'alias': 'test_motor', 'duration': 0.5})

        # Give it a moment then check status - end_time should be null for indefinite
        time.sleep(0.2)
        status = get_json('/api/status')
        print('Status snapshot:', status)

        # Now stop alias
        post_json('/api/stop', {'alias': 'test_motor'})

        # Add a group that turns OFF (example: lights_off)
        post_json('/api/config/groups', {'name': 'test_off_group', 'aliases': ['led_1', 'led_2'], 'action': 'off'})

        # Activate group (action=off) - should turn pins off
        post_json('/api/activate-group', {'group': 'test_off_group', 'duration': 0.5})

        # Cleanup: Delete alias
        r = requests.delete(BASE + '/api/config/aliases', json={'name': 'test_motor'})
        print('/api/config/aliases DELETE', r.status_code, r.text)
        r.raise_for_status()

        # Delete mapping
        r = requests.delete(BASE + '/api/config/gpio-pins', json={'config_spot': 'config_spot27'})
        print('/api/config/gpio-pins DELETE', r.status_code, r.text)
        r.raise_for_status()

        # Delete group
        r = requests.delete(BASE + '/api/config/groups', json={'name': 'test_off_group'})
        print('/api/config/groups DELETE', r.status_code, r.text)
        r.raise_for_status()

        # Reload config
        r = requests.post(BASE + '/api/config/reload')
        print('/api/config/reload', r.status_code, r.text)
        r.raise_for_status()

        print('\nIntegration test completed successfully')
    except Exception as e:
        print('Integration test FAILED:', e)


if __name__ == '__main__':
    main()
