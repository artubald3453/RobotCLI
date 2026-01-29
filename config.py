# ==============================
# RobotCLI Default Config
# ==============================


# ---- Physical GPIO bindings ----
# These are the ONLY real pin numbers in the entire system.
# Change these to match your wiring.

GPIO_PINS = {
    "config_spot1":  2,
    "config_spot2":  3,
    "config_spot3":  4,
    "config_spot4":  5,
    "config_spot5":  6,
    "config_spot6":  7,
    "config_spot7":  8,
    "config_spot8":  9,
    "config_spot9":  10,
    "config_spot10": 11,
    "config_spot11": 12,
    "config_spot12": 13,
    "config_spot13": 14,
    "config_spot14": 15,
    "config_spot15": 16,
    "config_spot16": 17,
    "config_spot17": 18,
    "config_spot18": 19,
    "config_spot19": 20,
    "config_spot20": 21,
    "config_spot21": 22,
    "config_spot22": 23,
    "config_spot23": 24,
    "config_spot24": 25,
    "config_spot25": 26,
    "config_spot26": 27,
    "config_spot27": None,
}


# ---- User-friendly aliases ----
# These are the names the USER types into the terminal.
# Format:  "user_alias": "config_spotX"
# Format in terminal: user_alias(duration_in_seconds)

ALIASES = {
    "motor_1": "config_spot1",
    "motor_2": "config_spot2",
    "motor_3": "config_spot3",
    "motor_4": "config_spot4",

    "motor_5": "config_spot5",
    "motor_6": "config_spot6",
    "motor_7": "config_spot7",
    "motor_8": "config_spot8",

    "led_1":   "config_spot9",
    "led_2":   "config_spot10",

    "relay_1": "config_spot11",
    "relay_2": "config_spot12",

    "buzzer":  "config_spot13",

    "aux_1":   "config_spot14",
    "aux_2":   "config_spot15",
    "aux_3":   "config_spot16",

    "servo_1": "config_spot17",
    "servo_2": "config_spot18",

    "spare_1": "config_spot19",
    "spare_2": "config_spot20",
    "spare_3": "config_spot21",
    "spare_4": "config_spot22",
    "spare_5": "config_spot23",
    "spare_6": "config_spot24",
    "spare_7": "config_spot25",
    "spare_8": "config_spot26",
    "spare_9": "config_spot27",
}


# ---- Group actions / stacked aliases ----
# These are MACROS.
# They expand into multiple user aliases.
# Format: "group_name": ["alias", "alias", "alias"]
# Format in terminal: group_name(duration_in_seconds)

GROUPS = {
    # Basic movement (2-motor differential drive)
    "forward":  ["motor_1", "motor_2"],
    "backward": ["motor_3", "motor_4"],

    "left":  ["motor_1", "motor_4"],
    "right": ["motor_2", "motor_3"],

    "stop": ["motor_1", "motor_2", "motor_3", "motor_4"],


    # Lights
    "lights_on":  ["led_1", "led_2"],
    "lights_off": ["led_1", "led_2"],


    # Alert modes
    "alarm": ["buzzer", "led_1", "led_2"],


    # All motors at once
    "all_motors": [
        "motor_1", "motor_2", "motor_3", "motor_4",
        "motor_5", "motor_6", "motor_7", "motor_8"
    ],


    # Everything ON (debug)
    "all_on": list(ALIASES.keys()),


    # Everything OFF (debug/safety)
    "all_off": list(ALIASES.keys()),
}

# ---- Persistent config storage (JSON) ----
import json
import os
import threading

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
_config_lock = threading.Lock()


def _save_json():
    with _config_lock:
        data = {
            'GPIO_PINS': GPIO_PINS,
            'ALIASES': ALIASES,
            'GROUPS': GROUPS,
        }
        tmp = CONFIG_FILE + '.tmp'
        try:
            with open(tmp, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
            os.replace(tmp, CONFIG_FILE)
        finally:
            # best-effort cleanup of tmp file if something went wrong
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass


def save_config():
    """Persist current configuration to disk (config.json)"""
    try:
        _save_json()
    except Exception as e:
        print(f"⚠️ Failed saving config to {CONFIG_FILE}: {e}")


def _load_json():
    """Load configuration from disk and overlay defaults."""
    if not os.path.exists(CONFIG_FILE):
        # Persist defaults so users can edit file later
        save_config()
        return
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
        gp = data.get('GPIO_PINS')
        if isinstance(gp, dict):
            for k, v in gp.items():
                GPIO_PINS[k] = v
        al = data.get('ALIASES')
        if isinstance(al, dict):
            ALIASES.clear()
            ALIASES.update(al)
        gr = data.get('GROUPS')
        if isinstance(gr, dict):
            GROUPS.clear()
            GROUPS.update(gr)
    except Exception as e:
        print(f"⚠️ Failed loading config from {CONFIG_FILE}: {e}")

# Load config at import time
_load_json()


def load_config():
    """Public wrapper to reload configuration from disk.

    Returns True on success, False on error.
    """
    try:
        _load_json()
        return True
    except Exception as e:
        print(f"⚠️ Failed reloading config: {e}")
        return False