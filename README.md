# RobotCLI

A command-line interface for controlling GPIO pins on a Raspberry Pi through user-friendly aliases.

## Overview

RobotCLI provides an easy way to control GPIO pins from the terminal without having to remember pin numbers. It maps friendly names (like `motor_1`, `led_2`, etc.) to actual GPIO pins and allows you to activate them for a specified duration.

## Features

- **User-friendly aliases** - Use memorable names instead of pin numbers
- **Timed activation** - Automatically deactivates pins after a specified duration
- **Group actions** - Create macros that activate multiple components at once
- **Easy configuration** - Edit `config.py` to customize pins and aliases
- **Interactive CLI** - Simple command interface for real-time control

## Usage

### Basic Command Format

```
alias_name(duration)
```

Where:
- `alias_name` is a user-friendly name (e.g., `motor_1`, `led_2`, `buzzer`)
- `duration` is how many seconds to keep the pin active

### Examples

```
motor_1(2.5)       # Run motor_1 for 2.5 seconds
buzzer(1)          # Activate buzzer for 1 second
led_1(0.5)         # Turn on led_1 for 0.5 seconds
servo_1(3)         # Activate servo_1 for 3 seconds
```

## Running the CLI

```bash
python3 parser.py
```

Then enter commands at the prompt:

```
>>> motor_1(2)
Activating motor_1 (pin 4) for 2 seconds...
Deactivated motor_1 (pin 4)

>>> led_2(1.5)
Activating led_2 (pin 20) for 1.5 seconds...
Deactivated led_2 (pin 20)

>>> quit
Exiting...
GPIO cleanup completed
```

## Running the Web GUI

Access your robot from any device on the network with a clean, modern interface:

### Setup (first time only)

```bash
pip3 install -r requirements-web.txt
```

### Start the Web Server

```bash
sudo python3 web_server.py
```

The server will start on **port 8000**. Access it from any device on your network:

```
http://<your-pi-ip>:8000
```

**Find your Pi's IP address:**
```bash
hostname -I
```

### Features

- 🎨 **Clean, Responsive GUI** - Works on desktop, tablet, and mobile
- 🌐 **Network Access** - Control from any device on your network
- ⏱️ **Adjustable Duration** - Set activation time in real-time with a slider
- 📦 **Grouped Controls** - Organize controls by motor, LED, relay, servo, etc.
- ⛔ **Emergency Stop** - One-click button to stop all components
- 📊 **Live Status** - See what's currently active

---

## REST API & Persistence

The web GUI is backed by a small REST API that lets you view and modify the configuration programmatically. All changes are persisted to `config.json` in the repository root so they survive server restarts.

Important notes:
- Valid BCM pin numbers are **2–27** (pins 0 and 1 are reserved for I2C and are not configured as outputs by default).
- When a config value is invalid it will be unset (set to `null` in `config.json`) and a warning will be printed on server start.

### Endpoints (examples)

- Get full config
  - GET `/api/config`

- Aliases
  - GET `/api/config/aliases`
  - POST `/api/config/aliases` { `"name": "alias_name", "config_spot": "config_spot1", "auto_off": true` }
  - DELETE `/api/config/aliases` { `"name": "alias_name"` }

- GPIO pin mappings
  - GET `/api/config/gpio-pins`
  - POST `/api/config/gpio-pins` { `"config_spot": "config_spot1", "pin_num": 4` }
  - DELETE `/api/config/gpio-pins` { `"config_spot": "config_spot1"` }

- Groups
  - GET `/api/config/groups`
  - POST `/api/config/groups` { `"name": "group_name", "aliases": ["alias1","alias2"], "action": "on" }`
  - DELETE `/api/config/groups` { `"name": "group_name"` }

- Activate
  - POST `/api/activate` { `"alias": "motor_1", "duration": 2.5` }  (honors alias `auto_off` setting)
  - POST `/api/activate-group` { `"group": "lights_on", "duration": 1.0` } (group `action` controls if group turns ON or OFF)

- Stop
  - POST `/api/stop` { `"alias": "motor_1"` } (or omit `alias` to stop everything)

- Reload config from disk
  - POST `/api/config/reload`  (reloads `config.json`, unsets invalid mappings, and persists corrections)

### Quick curl examples

```bash
# Map config_spot27 to pin 26
curl -X POST -H "Content-Type: application/json" -d '{"config_spot": "config_spot27", "pin_num": 26}' http://<pi-ip>:8000/api/config/gpio-pins

# Add an alias
curl -X POST -H "Content-Type: application/json" -d '{"name": "new_motor", "config_spot": "config_spot27"}' http://<pi-ip>:8000/api/config/aliases

# Activate alias for 2 seconds
curl -X POST -H "Content-Type: application/json" -d '{"alias": "new_motor", "duration": 2}' http://<pi-ip>:8000/api/activate

# Delete an alias
curl -X DELETE -H "Content-Type: application/json" -d '{"name": "new_motor"}' http://<pi-ip>:8000/api/config/aliases

# Reload config (re-reads config.json and unsets invalid mappings)
curl -X POST http://<pi-ip>:8000/api/config/reload
```

---

## Running the integration test

1. Start the web server: `sudo python3 web_server.py`
2. Install requirements: `pip3 install requests`
3. Run: `python3 tests/integration_test.py`

The test will perform a small sequence of API calls (map a pin, add an alias, activate, stop, delete, reload).



## Configuration

Edit `config.py` to customize your setup:

### GPIO_PINS

Maps hardware configuration names to actual GPIO pin numbers. **These are the only real pin numbers in the system** — update these to match your wiring:

```python
GPIO_PINS = {
    "config_spot1": 4,
    "config_spot2": 5,
    # ... etc
}
```

### ALIASES

Maps user-friendly names to configuration spots. This is what you type in the terminal:

```python
ALIASES = {
    "motor_1": "config_spot1",
    "motor_2": "config_spot2",
    "led_1": "config_spot9",
    # ... etc
}
```

### GROUPS

Define macros that activate multiple components at once (for future use):

```python
GROUPS = {
    "forward": ["motor_1", "motor_2"],
    "stop": ["motor_1", "motor_2", "motor_3", "motor_4"],
    # ... etc
}
```

## File Structure

- **config.py** - Configuration file with GPIO mappings, aliases, and groups
- **parser.py** - Main CLI interface that accepts and executes commands
- **pinrun.py** - Low-level GPIO control functions for each pin
- **web_server.py** - Flask web server for network-based GUI control
- **templates/index.html** - Responsive web interface for controlling GPIO pins
- **requirements-web.txt** - Python dependencies for the web server

## Requirements

### Core
- Raspberry Pi with GPIO pins
- Python 3
- RPi.GPIO library: `sudo apt-get install python3-rpi.gpio`

### Web GUI (Optional)
- Flask: `pip3 install Flask==2.3.0`

## Installation

### Core Setup
```bash
sudo apt-get install python3-rpi.gpio
```

### Web GUI Setup (Optional)
```bash
pip3 install -r requirements-web.txt
```

## Customization

### Add a new component

1. Wire the component to a GPIO pin on your Raspberry Pi
2. Find the BCM pin number
3. Add an entry to `GPIO_PINS` in `config.py`
4. Add an alias in `ALIASES` that maps your user-friendly name to the config spot
5. Start using it immediately!

**Example:** Adding a new motor on pin 7:

```python
GPIO_PINS = {
    # ... existing pins
    "config_spot24": 7,  # New motor on pin 7
}

ALIASES = {
    # ... existing aliases
    "motor_new": "config_spot24",  # User-friendly name
}
```

Then run: `motor_new(5)`

## Troubleshooting

- **"Unknown alias" error** - Check that the alias is defined in `ALIASES` in `config.py`
- **GPIO errors** - Make sure you're running as root: `sudo python3 parser.py`
- **Invalid format** - Ensure command is formatted as `alias_name(duration)` with no spaces

## Future Roadmap

### Recently Completed ✅
- **Web UI Dashboard** - Visual interface to monitor and control pins in real-time
- **REST API Integration** - Control GPIO pins via HTTP endpoints for remote operation

### Planned Features

- **Batch Command Execution** - Run multiple commands in sequence from a script file
- **Conditional Logic** - Add if/else statements for automated workflows
- **Timing & Scheduling** - Schedule commands to run at specific times or intervals
- **Status Monitoring** - Query current pin states and get feedback on component status
- **Event Logging** - Log all commands and GPIO state changes to a file for debugging and auditing
- **Python Library Export** - Package RobotCLI as a Python module for use in other projects
- **Error Recovery** - Automatic recovery from GPIO errors and connection issues
- **Performance Metrics** - Track execution times and performance data
- **AI API Control** - Integrate with AI APIs and let them use RobotCLI!
- **Performance Metrics** - Track execution times and performance data
- **AI API controll** - API any AI you want and let it use RobotCLI!

## AI Integration
You can register an API key and model in the web UI (open the `AI` tab). The server exposes endpoints:

- `GET /api/ai/config` — returns current AI configuration (key masked)
- `POST /api/ai/register` — register/update API key/model (`{ api_key, model, enabled }`)
- `GET /api/ai/schema` — returns a JSON Schema that describes valid AI commands (auto-updates based on configured aliases/groups)
- `POST /api/ai/execute` — execute a command (`{ api_key?, command: { action, target?, duration? } }`). API key may be supplied in body or Authorization header as `Bearer <key>`.

The AI JSON Schema is generated from your current `ALIASES` and `GROUPS` so the AI only sees valid actions. The user only needs to enter an API key and model in the web UI to enable AI access.

Chat UI
-------
A chat interface is available under the **AI** tab in the web UI. Type natural language requests and the configured model will reply with a short human-friendly message (e.g., "Okay, pin moving"). The model is instructed to return a JSON payload of commands; the server validates and executes those commands (single or multiple).

OpenAI compatibility
--------------------
RobotCLI is compatible with **OpenAI-compatible** chat APIs by default. The server proxies requests to an OpenAI-style chat completion endpoint and expects the configured model to be an OpenAI-compatible model (for example: `gpt-4`, `gpt-4o-mini`, `gpt-4-mini`). Set the model under the AI settings in the web UI.

Expected model output (JSON)
---------------------------
The model is prompted to return a compact JSON object only, for example:

{
  "response": "Okay, turning on the lights",
  "commands": [
    { "action": "activate_alias", "target": "led_1", "duration": 2 }
  ]
}

The server will validate and execute any commands present in the `commands` array and return a short reply to show in the chat UI. You can optionally enable "Share past conversation with model" in the AI chat UI so the model can use previous messages for context; this is sent to the provider as part of the chat request and is limited to recent messages.

Security & Disclaimer
---------------------
By entering your API key into the RobotCLI UI, you accept responsibility for its security. RobotCLI stores the key locally in `config.json` and will use it to proxy requests to the model provider. The project is not responsible for API key compromise or misuse — secure your device and network appropriately.

An example client script is included at `ai_client.py` showing how to register and call the schema/execute endpoints.