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
from config import GPIO_PINS, ALIASES, GROUPS

app = Flask(__name__)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
for pin in range(2, 28):
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


@app.route('/api/activate', methods=['POST'])
def activate():
    """Activate an alias for specified duration"""
    data = request.json
    alias = data.get('alias')
    duration = float(data.get('duration', 1.0))
    
    if alias not in ALIASES:
        return jsonify({'error': 'Unknown alias'}), 400
    
    config_spot = ALIASES[alias]
    pin_num = GPIO_PINS[config_spot]
    
    activate_pin(pin_num, duration)
    
    return jsonify({
        'success': True,
        'alias': alias,
        'pin': pin_num,
        'duration': duration
    })


@app.route('/api/activate-group', methods=['POST'])
def activate_group():
    """Activate all pins in a group"""
    data = request.json
    group = data.get('group')
    duration = float(data.get('duration', 1.0))
    
    if group not in GROUPS:
        return jsonify({'error': 'Unknown group'}), 400
    
    aliases = GROUPS[group]
    activated = []
    
    for alias in aliases:
        if alias in ALIASES:
            config_spot = ALIASES[alias]
            pin_num = GPIO_PINS[config_spot]
            activate_pin(pin_num, duration)
            activated.append({'alias': alias, 'pin': pin_num})
    
    return jsonify({
        'success': True,
        'group': group,
        'activated': activated,
        'duration': duration
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get status of all active pins"""
    with lock:
        status = {}
        current_time = time.time()
        for pin_num, end_time in active_pins.items():
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
        pin_num = GPIO_PINS[config_spot]
        
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
