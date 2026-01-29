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

# ALIASES maps friendly names to a dictionary with config spot and options
# Format: "alias": { "config_spot": "config_spotX", "auto_off": True }
# Backwards compatibility: strings will be accepted and converted at load time.
ALIASES = {
    "motor_1": {"config_spot": "config_spot1", "auto_off": True},
    "motor_2": {"config_spot": "config_spot2", "auto_off": True},
    "motor_3": {"config_spot": "config_spot3", "auto_off": True},
    "motor_4": {"config_spot": "config_spot4", "auto_off": True},

    "motor_5": {"config_spot": "config_spot5", "auto_off": True},
    "motor_6": {"config_spot": "config_spot6", "auto_off": True},
    "motor_7": {"config_spot": "config_spot7", "auto_off": True},
    "motor_8": {"config_spot": "config_spot8", "auto_off": True},

    "led_1":   {"config_spot": "config_spot9", "auto_off": True},
    "led_2":   {"config_spot": "config_spot10", "auto_off": True},

    "relay_1": {"config_spot": "config_spot11", "auto_off": True},
    "relay_2": {"config_spot": "config_spot12", "auto_off": True},

    "buzzer":  {"config_spot": "config_spot13", "auto_off": True},

    "aux_1":   {"config_spot": "config_spot14", "auto_off": True},
    "aux_2":   {"config_spot": "config_spot15", "auto_off": True},
    "aux_3":   {"config_spot": "config_spot16", "auto_off": True},

    "servo_1": {"config_spot": "config_spot17", "auto_off": True},
    "servo_2": {"config_spot": "config_spot18", "auto_off": True},

    "spare_1": {"config_spot": "config_spot19", "auto_off": True},
    "spare_2": {"config_spot": "config_spot20", "auto_off": True},
    "spare_3": {"config_spot": "config_spot21", "auto_off": True},
    "spare_4": {"config_spot": "config_spot22", "auto_off": True},
    "spare_5": {"config_spot": "config_spot23", "auto_off": True},
    "spare_6": {"config_spot": "config_spot24", "auto_off": True},
    "spare_7": {"config_spot": "config_spot25", "auto_off": True},
    "spare_8": {"config_spot": "config_spot26", "auto_off": True},
    "spare_9": {"config_spot": "config_spot27", "auto_off": True},
}


# ---- Group actions / stacked aliases ----
# These are MACROS.
# They expand into multiple user aliases.
# Format: "group_name": ["alias", "alias", "alias"]
# Format in terminal: group_name(duration_in_seconds)

# GROUPS map a group name to either a list of aliases (legacy) or a dict:
# "group_name": { "aliases": ["alias1", ...], "action": "on"|"off" }
# Legacy list form will be converted at load time with default action="on".
GROUPS = {
    # Basic movement (2-motor differential drive)
    "forward": {"aliases": ["motor_1", "motor_2"], "action": "on"},
    "backward": {"aliases": ["motor_3", "motor_4"], "action": "on"},

    "left": {"aliases": ["motor_1", "motor_4"], "action": "on"},
    "right": {"aliases": ["motor_2", "motor_3"], "action": "on"},

    "stop": {"aliases": ["motor_1", "motor_2", "motor_3", "motor_4"], "action": "off"},

    # Lights
    "lights_on": {"aliases": ["led_1", "led_2"], "action": "on"},
    "lights_off": {"aliases": ["led_1", "led_2"], "action": "off"},

    # Alert modes
    "alarm": {"aliases": ["buzzer", "led_1", "led_2"], "action": "on"},

    # All motors at once
    "all_motors": {"aliases": [
        "motor_1", "motor_2", "motor_3", "motor_4",
        "motor_5", "motor_6", "motor_7", "motor_8"
    ], "action": "on"},

    # Everything ON (debug)
    "all_on": {"aliases": list(ALIASES.keys()), "action": "on"},

    # Everything OFF (debug/safety)
    "all_off": {"aliases": list(ALIASES.keys()), "action": "off"},
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
    """Load configuration from disk and overlay defaults.

    Also perform compatibility fixes:
    - Convert string alias values into dicts with auto_off=True
    - Convert legacy group list into dict with action='on'
    """
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
            # normalize alias format
            for k, v in al.items():
                if isinstance(v, str):
                    ALIASES[k] = {'config_spot': v, 'auto_off': True}
                elif isinstance(v, dict):
                    # ensure auto_off exists
                    ALIASES[k] = {'config_spot': v.get('config_spot'), 'auto_off': bool(v.get('auto_off', True))}
        gr = data.get('GROUPS')
        if isinstance(gr, dict):
            GROUPS.clear()
            for k, v in gr.items():
                if isinstance(v, list):
                    GROUPS[k] = {'aliases': v, 'action': 'on'}
                elif isinstance(v, dict):
                    GROUPS[k] = {'aliases': v.get('aliases', []), 'action': v.get('action', 'on')}
    except Exception as e:
        print(f"⚠️ Failed loading config from {CONFIG_FILE}: {e}")
    # Save normalized structure back to disk so config.json is consistent
    try:
        save_config()
    except Exception:
        pass

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