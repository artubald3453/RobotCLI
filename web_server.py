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
from config import GPIO_PINS, ALIASES, GROUPS, save_config, load_config

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
