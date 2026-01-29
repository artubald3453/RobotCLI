#!/usr/bin/env python3
"""
RobotCLI Web Server - Access GPIO controls via a network GUI
Run: python3 web_server.py
Access at: http://<your-pi-ip>:8000
"""

from flask import Flask, render_template, jsonify, request
import RPi.GPIO as GPIO
import threading
import time
import requests
import json
from config import GPIO_PINS, ALIASES, GROUPS, AI_SETTINGS, save_config, load_config

app = Flask(__name__)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
# Note: GPIO 0 and 1 are reserved for I2C, pins 2-27 are standard GPIO
VALID_PINS = set(range(2, 28))

# Validate existing mappings in config (unset invalid entries)
invalid_spots = []
for k, v in list(GPIO_PINS.items()):
    if not isinstance(v, int) or v not in VALID_PINS:
        invalid_spots.append(k)
        GPIO_PINS[k] = None
if invalid_spots:
    print(f"⚠️ Invalid GPIO mappings for: {invalid_spots}. They have been unset (set to None).")
    # Persist the changes so they survive a restart
    save_config()

for pin in VALID_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Track active pins for status
active_pins = {}
lock = threading.Lock()


def activate_pin(pin_num, duration):
    """Activate a pin for specified duration"""
    with lock:
        GPIO.output(pin_num, GPIO.HIGH)
        active_pins[pin_num] = time.time() + duration
    
    # Deactivate after duration
    def deactivate():
        time.sleep(duration)
        with lock:
            GPIO.output(pin_num, GPIO.LOW)
            if pin_num in active_pins:
                del active_pins[pin_num]
    
    thread = threading.Thread(target=deactivate, daemon=True)
    thread.start()


@app.route('/')
def index():
    """Serve the main GUI"""
    return render_template('index.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """Return aliases and groups configuration"""
    return jsonify({
        'aliases': ALIASES,
        'groups': GROUPS,
        'gpio_pins': GPIO_PINS
    })


# ---- AI Integration Endpoints ----
def generate_ai_schema():
    """Dynamically generate a JSON Schema that describes valid AI commands.

    The schema auto-updates based on configured aliases and groups so the
    AI can discover exactly what it can control. Additionally supports
    an array-of-commands payload for multi-command execution.
    """
    aliases = list(ALIASES.keys())
    groups = list(GROUPS.keys())

    single_cmd = {
        'title': 'RobotCLI AI Single Command',
        'type': 'object',
        'properties': {
            'action': {'type': 'string', 'enum': ['activate_alias', 'activate_group', 'stop', 'status']},
            'target': {'type': 'string'},
            'duration': {'type': 'number', 'minimum': 0.0},
        },
        'required': ['action'],
        'oneOf': [
            {
                'properties': {
                    'action': {'const': 'activate_alias'},
                    'target': {'enum': aliases},
                    'duration': {'type': 'number', 'minimum': 0.1}
                },
                'required': ['action', 'target']
            },
            {
                'properties': {
                    'action': {'const': 'activate_group'},
                    'target': {'enum': groups},
                    'duration': {'type': 'number', 'minimum': 0.1}
                },
                'required': ['action', 'target']
            },
            {
                'properties': {
                    'action': {'const': 'stop'},
                    'target': {'enum': aliases + groups}
                },
                'required': ['action', 'target']
            },
            {
                'properties': {
                    'action': {'const': 'status'}
                },
                'required': ['action']
            }
        ]
    }

    schema = {
        'title': 'RobotCLI AI Command Schema',
        'description': 'Either a single command object or an array of command objects (multi-command).',
        'oneOf': [
            single_cmd,
            {
                'type': 'array',
                'items': single_cmd,
                'minItems': 1
            }
        ]
    }
    return schema


@app.route('/api/ai/config', methods=['GET'])
def get_ai_config():
    """Return current AI configuration (key masked)."""
    masked = AI_SETTINGS.copy()
    if masked.get('api_key'):
        masked['api_key'] = '****' + (masked['api_key'][-4:] if isinstance(masked['api_key'], str) else '')
    return jsonify(masked)


@app.route('/api/ai/register', methods=['POST'])
def register_ai():
    """Register or update AI settings (key, model, enabled)."""
    data = request.json or {}
    api_key = data.get('api_key')
    model = data.get('model')
    enabled = bool(data.get('enabled', True))

    AI_SETTINGS['api_key'] = api_key
    AI_SETTINGS['model'] = model
    AI_SETTINGS['enabled'] = enabled
    save_config()

    masked_key = None
    if AI_SETTINGS.get('api_key'):
        ak = AI_SETTINGS['api_key']
        masked_key = '****' + (ak[-4:] if isinstance(ak, str) and len(ak) > 4 else '')

    return jsonify({'success': True, 'ai': {
        'enabled': AI_SETTINGS['enabled'],
        'model': AI_SETTINGS['model'],
        'api_key': masked_key
    }})


@app.route('/api/ai/schema', methods=['GET'])
def get_ai_schema():
    """Return the generated JSON schema for AI commands."""
    return jsonify(generate_ai_schema())


@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Accept natural language from a user (or AI) and proxy to the configured model.

    The model is instructed to reply with a short human-friendly message ("response")
    and a JSON array "commands" containing one or more commands that conform to
    the generated schema. The server will validate/parse and execute those commands
    safely (simple validation), then return the model's response back to the UI.
    """
    data = request.json or {}
    user_msg = data.get('message')
    # For chat coming from the local UI we use the stored AI_SETTINGS api key
    # and therefore do not require the caller to present the key. We still
    # require AI integration to be enabled and a server-side API key to exist.
    if not AI_SETTINGS.get('enabled'):
        return jsonify({'error': 'AI access disabled'}), 400
    if not AI_SETTINGS.get('api_key'):
        return jsonify({'error': 'AI API key not configured on server'}), 400
    if not user_msg:
        return jsonify({'error': 'Missing message'}), 400

    # Build a system prompt that instructs the model to respond with JSON
    system_prompt = (
        "You are a RobotCLI assistant. When given a user instruction, produce a JSON object only. "
        "Format exactly as: {\"response\":\"<short human-readable reply>\", \"commands\": [ ... ]}. "
        "Commands must follow the RobotCLI AI Command Schema: actions: activate_alias, activate_group, stop, status. "
        "Return no additional text, explanation, or code fences. Keep the response short (one sentence)."
    )

    # Prepare messages for OpenAI-like chat completion
    messages = [
        { 'role': 'system', 'content': system_prompt },
        { 'role': 'user', 'content': user_msg }
    ]

    # Call provider (OpenAI-compatible)
    try:
        resp = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': 'Bearer ' + AI_SETTINGS['api_key'],
                'Content-Type': 'application/json'
            },
            json={
                'model': AI_SETTINGS.get('model') or 'gpt-4o-mini',
                'messages': messages,
                'temperature': 0.0,
                'max_tokens': 512
            },
            timeout=20
        )
    except Exception as e:
        return jsonify({'error': f'Provider request failed: {e}'}), 502

    if resp.status_code != 200:
        return jsonify({'error': 'Provider returned error', 'details': resp.text}), 502

    try:
        body = resp.json()
        content = body['choices'][0]['message']['content']
    except Exception as e:
        return jsonify({'error': 'Malformed provider response', 'details': str(e)}), 502

    # Extract JSON object from content
    parsed = None
    try:
        parsed = json.loads(content)
    except Exception:
        # Try to locate a JSON block inside the text
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(content[start:end+1])
            except Exception:
                parsed = None

    if not parsed or 'response' not in parsed:
        return jsonify({'error': 'Provider did not return valid JSON with `response`', 'raw': content}), 502

    # Validate and execute commands if present
    commands = parsed.get('commands', [])
    executed = []
    if isinstance(commands, dict):
        commands = [commands]
    for cmd in commands:
        # Basic validation: must have action
        if not isinstance(cmd, dict) or 'action' not in cmd:
            executed.append({'error': 'Invalid command format', 'cmd': cmd})
            continue
        res = _execute_single_command(cmd)
        executed.append(res)

    # Return only the model's short reply to the UI plus execution report
    return jsonify({'reply': parsed.get('response'), 'executed': executed})


def _execute_single_command(cmd):
    """Execute a single normalized command dict and return result dict."""
    action = cmd.get('action')
    target = cmd.get('target')
    duration = float(cmd.get('duration', 1.0)) if cmd.get('duration') is not None else 1.0

    if action == 'activate_alias':
        if target not in ALIASES:
            return {'error': 'Unknown alias', 'cmd': cmd}
        a = ALIASES[target]
        if isinstance(a, str):
            config_spot = a
            auto_off = True
        else:
            config_spot = a.get('config_spot')
            auto_off = bool(a.get('auto_off', True))
        pin_num = GPIO_PINS.get(config_spot)
        if pin_num is None or pin_num not in VALID_PINS:
            return {'error': 'Alias not mapped to a valid pin', 'cmd': cmd}
        if auto_off:
            activate_pin(pin_num, duration)
        else:
            with lock:
                GPIO.output(pin_num, GPIO.HIGH)
                active_pins[pin_num] = None
        return {'success': True, 'action': action, 'alias': target, 'duration': duration}

    if action == 'activate_group':
        if target not in GROUPS:
            return {'error': 'Unknown group', 'cmd': cmd}
        grp = GROUPS[target]
        aliases = grp.get('aliases', []) if isinstance(grp, dict) else grp
        activated = []
        for alias in aliases:
            if alias in ALIASES:
                a = ALIASES[alias]
                if isinstance(a, str):
                    config_spot = a
                    auto_off = True
                else:
                    config_spot = a.get('config_spot')
                    auto_off = bool(a.get('auto_off', True))
                pin_num = GPIO_PINS.get(config_spot)
                if pin_num is None or pin_num not in VALID_PINS:
                    continue
                if auto_off:
                    activate_pin(pin_num, duration)
                else:
                    with lock:
                        GPIO.output(pin_num, GPIO.HIGH)
                        active_pins[pin_num] = None
                activated.append({'alias': alias, 'pin': pin_num})
        return {'success': True, 'action': action, 'group': target, 'activated': activated, 'duration': duration}

    if action == 'stop':
        # target may be alias or group
        if target in ALIASES:
            a = ALIASES[target]
            config_spot = a.get('config_spot') if isinstance(a, dict) else a
            pin_num = GPIO_PINS.get(config_spot)
            if pin_num is None:
                return {'error': 'Alias not mapped to a valid GPIO pin', 'cmd': cmd}
            with lock:
                GPIO.output(pin_num, GPIO.LOW)
                if pin_num in active_pins:
                    del active_pins[pin_num]
            return {'success': True, 'stopped': target}
        elif target in GROUPS:
            grp = GROUPS[target]
            aliases = grp.get('aliases', []) if isinstance(grp, dict) else grp
            stopped = []
            for alias in aliases:
                if alias in ALIASES:
                    a = ALIASES[alias]
                    config_spot = a.get('config_spot') if isinstance(a, dict) else a
                    pin_num = GPIO_PINS.get(config_spot)
                    if pin_num is None:
                        continue
                    with lock:
                        GPIO.output(pin_num, GPIO.LOW)
                        if pin_num in active_pins:
                            del active_pins[pin_num]
                    stopped.append(alias)
            return {'success': True, 'stopped': stopped}
        else:
            return {'error': 'Unknown target for stop', 'cmd': cmd}

    if action == 'status':
        with lock:
            status = {}
            current_time = time.time()
            for pin_num, end_time in active_pins.items():
                if end_time is None:
                    status[str(pin_num)] = None
                else:
                    remaining = max(0, end_time - current_time)
                    status[str(pin_num)] = remaining
        return {'success': True, 'status': status}

    return {'error': 'Unknown action', 'cmd': cmd}


@app.route('/api/ai/execute', methods=['POST'])
def ai_execute():
    """Allow an authorized AI to execute a command described by the schema.

    Supports a single `command` or an array `commands` (multi-command).
    Requires AI to be enabled and the provided api_key to match the configured key.
    """
    data = request.json or {}
    api_key = data.get('api_key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if not AI_SETTINGS.get('enabled'):
        return jsonify({'error': 'AI access disabled'}), 400
    if not AI_SETTINGS.get('api_key'):
        return jsonify({'error': 'AI API key not configured on server'}), 400
    if api_key != AI_SETTINGS.get('api_key'):
        return jsonify({'error': 'Unauthorized'}), 401

    # Accept either a single command or an array of commands
    commands = []
    if 'commands' in data:
        commands = data.get('commands') or []
    elif 'command' in data:
        commands = [data.get('command')]
    else:
        return jsonify({'error': 'Missing command(s)'}), 400

    results = []
    for cmd in commands:
        results.append(_execute_single_command(cmd))

    return jsonify({'success': True, 'results': results})


@app.route('/api/config/reload', methods=['POST'])
def reload_config():
    """Reload config.json from disk and re-validate mappings"""
    success = load_config()

    # Re-validate mappings and unset invalid entries
    invalid_spots = []
    for k, v in list(GPIO_PINS.items()):
        if not isinstance(v, int) or v not in VALID_PINS:
            if v is not None:
                invalid_spots.append(k)
            GPIO_PINS[k] = None

    if invalid_spots:
        # Persist corrected state
        save_config()

    return jsonify({
        'success': bool(success),
        'invalid': invalid_spots,
        'gpio_pins': GPIO_PINS,
        'aliases': ALIASES,
        'groups': GROUPS,
    })


@app.route('/api/config/aliases', methods=['GET', 'POST', 'DELETE'])
def manage_aliases():
    """Get, add/update, or remove aliases

    Alias format:
      { 'name': 'alias', 'config_spot': 'config_spot1', 'auto_off': true }
    """
    if request.method == 'GET':
        return jsonify(ALIASES)
    
    if request.method == 'DELETE':
        data = request.json or {}
        alias_name = data.get('name')
        if not alias_name:
            return jsonify({'error': 'Missing name'}), 400
        if alias_name in ALIASES:
            del ALIASES[alias_name]
            save_config()
            return jsonify({'success': True, 'deleted': alias_name})
        else:
            return jsonify({'error': 'Unknown alias'}), 400
    
    # POST - update/add an alias
    data = request.json
    alias_name = data.get('name')
    config_spot = data.get('config_spot')
    auto_off = data.get('auto_off', True)
    
    if not alias_name or not config_spot:
        return jsonify({'error': 'Missing name or config_spot'}), 400
    
    if config_spot not in GPIO_PINS:
        return jsonify({'error': 'Invalid config_spot'}), 400
    
    try:
        auto_off = bool(auto_off)
    except Exception:
        auto_off = True
    
    ALIASES[alias_name] = {'config_spot': config_spot, 'auto_off': auto_off}
    save_config()
    return jsonify({'success': True, 'alias': alias_name, 'config_spot': config_spot, 'auto_off': auto_off})


@app.route('/api/config/gpio-pins', methods=['GET', 'POST', 'DELETE'])
def manage_gpio_pins():
    """Get, add/update, or remove GPIO pin mappings"""
    if request.method == 'GET':
        return jsonify(GPIO_PINS)
    
    if request.method == 'DELETE':
        data = request.json or {}
        config_spot = data.get('config_spot')
        if not config_spot:
            return jsonify({'error': 'Missing config_spot'}), 400
        if config_spot in GPIO_PINS:
            GPIO_PINS[config_spot] = None
            save_config()
            return jsonify({'success': True, 'config_spot': config_spot, 'pin_num': None})
        else:
            return jsonify({'error': 'Unknown config_spot'}), 400
    
    # POST - update a GPIO pin mapping
    data = request.json
    config_spot = data.get('config_spot')
    try:
        pin_num = int(data.get('pin_num', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid pin_num'}), 400
    
    if not config_spot:
        return jsonify({'error': 'Missing config_spot'}), 400
    
    if pin_num < 2 or pin_num > 27:
        return jsonify({'error': 'Pin number must be between 2 and 27'}), 400
    
    GPIO_PINS[config_spot] = pin_num
    save_config()
    return jsonify({'success': True, 'config_spot': config_spot, 'pin_num': pin_num})


@app.route('/api/config/groups', methods=['GET', 'POST', 'DELETE'])
def manage_groups():
    """Get, add/update, or remove groups

    Group format:
      { 'name': 'group', 'aliases': ['a','b'], 'action': 'on'|'off' }
    """
    if request.method == 'GET':
        return jsonify(GROUPS)
    
    if request.method == 'DELETE':
        data = request.json or {}
        group_name = data.get('name')
        if not group_name:
            return jsonify({'error': 'Missing group name'}), 400
        if group_name in GROUPS:
            del GROUPS[group_name]
            save_config()
            return jsonify({'success': True, 'deleted': group_name})
        else:
            return jsonify({'error': 'Unknown group'}), 400
    
    # POST - update a group
    data = request.json
    group_name = data.get('name')
    aliases_list = data.get('aliases', [])
    action = data.get('action', 'on')
    
    if not group_name:
        return jsonify({'error': 'Missing group name'}), 400
    
    # Validate all aliases exist
    for alias in aliases_list:
        if alias not in ALIASES:
            return jsonify({'error': f'Unknown alias: {alias}'}), 400
    
    if action not in ('on', 'off'):
        return jsonify({'error': 'Invalid action; must be "on" or "off"'}), 400
    
    GROUPS[group_name] = {'aliases': aliases_list, 'action': action}
    save_config()
    return jsonify({'success': True, 'group': group_name, 'aliases': aliases_list, 'action': action})


@app.route('/api/activate', methods=['POST'])
def activate():
    """Activate an alias for specified duration. Respects per-alias `auto_off` setting."""
    data = request.json
    alias = data.get('alias')
    duration = float(data.get('duration', 1.0))
    
    if alias not in ALIASES:
        return jsonify({'error': 'Unknown alias'}), 400
    # alias may be dict
    a = ALIASES[alias]
    if isinstance(a, str):
        config_spot = a
        auto_off = True
    else:
        config_spot = a.get('config_spot')
        auto_off = bool(a.get('auto_off', True))
    
    pin_num = GPIO_PINS.get(config_spot)
    
    if pin_num is None:
        return jsonify({'error': 'Alias not mapped to a valid GPIO pin'}), 400
    if pin_num not in VALID_PINS:
        return jsonify({'error': 'Configured pin is invalid'}), 400
    
    if auto_off:
        activate_pin(pin_num, duration)
    else:
        # Set indefinitely until manually stopped
        with lock:
            GPIO.output(pin_num, GPIO.HIGH)
            active_pins[pin_num] = None
    
    return jsonify({
        'success': True,
        'alias': alias,
        'pin': pin_num,
        'duration': duration,
        'auto_off': auto_off
    })


@app.route('/api/activate-group', methods=['POST'])
def activate_group():
    """Activate or deactivate all pins in a group depending on group's `action`"""
    data = request.json
    group = data.get('group')
    duration = float(data.get('duration', 1.0))
    
    if group not in GROUPS:
        return jsonify({'error': 'Unknown group'}), 400
    
    grp = GROUPS[group]
    if isinstance(grp, list):
        aliases = grp
        action = 'on'
    else:
        aliases = grp.get('aliases', [])
        action = grp.get('action', 'on')

    activated = []
    
    for alias in aliases:
        if alias in ALIASES:
            a = ALIASES[alias]
            if isinstance(a, str):
                config_spot = a
                auto_off = True
            else:
                config_spot = a.get('config_spot')
                auto_off = bool(a.get('auto_off', True))
            pin_num = GPIO_PINS.get(config_spot)
            if pin_num is None or pin_num not in VALID_PINS:
                continue
            if action == 'on':
                if auto_off:
                    activate_pin(pin_num, duration)
                else:
                    with lock:
                        GPIO.output(pin_num, GPIO.HIGH)
                        active_pins[pin_num] = None
                activated.append({'alias': alias, 'pin': pin_num})
            else:
                # action == 'off'
                with lock:
                    GPIO.output(pin_num, GPIO.LOW)
                    if pin_num in active_pins:
                        del active_pins[pin_num]
                activated.append({'alias': alias, 'pin': pin_num})
    
    return jsonify({
        'success': True,
        'group': group,
        'activated': activated,
        'duration': duration,
        'action': action
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get status of all active pins"""
    with lock:
        status = {}
        current_time = time.time()
        for pin_num, end_time in active_pins.items():
            if end_time is None:
                status[str(pin_num)] = None
            else:
                remaining = max(0, end_time - current_time)
                status[str(pin_num)] = remaining
    
    return jsonify(status)


@app.route('/api/stop', methods=['POST'])
def stop():
    """Stop a specific pin or all pins"""
    data = request.json
    alias = data.get('alias')
    
    if alias:
        if alias not in ALIASES:
            return jsonify({'error': 'Unknown alias'}), 400
        
        config_spot = ALIASES[alias]
        pin_num = GPIO_PINS.get(config_spot)
        if pin_num is None:
            return jsonify({'error': 'Alias not mapped to a valid GPIO pin'}), 400
        
        with lock:
            GPIO.output(pin_num, GPIO.LOW)
            if pin_num in active_pins:
                del active_pins[pin_num]
        
        return jsonify({'success': True, 'alias': alias, 'pin': pin_num})
    else:
        # Stop all
        with lock:
            for pin_num in active_pins.keys():
                GPIO.output(pin_num, GPIO.LOW)
            active_pins.clear()
        
        return jsonify({'success': True, 'message': 'All pins stopped'})


if __name__ == '__main__':
    try:
        print("🤖 RobotCLI Web Server starting...")
        print("📡 Access at: http://<your-pi-ip>:8000")
        app.run(host='0.0.0.0', port=8000, debug=False)
    finally:
        GPIO.cleanup()
        print("\n✋ GPIO cleanup completed")
