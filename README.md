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