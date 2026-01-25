# ==============================
# RobotCLI Default Config
# ==============================


# ---- Physical GPIO bindings ----
# These are the ONLY real pin numbers in the entire system.
# Change these to match your wiring.

GPIO_PINS = {
    "config_spot1":  4,
    "config_spot2":  5,
    "config_spot3":  6,
    "config_spot4":  12,
    "config_spot5":  13,
    "config_spot6":  16,
    "config_spot7":  17,
    "config_spot8":  18,
    "config_spot9":  19,
    "config_spot10": 20,
    "config_spot11": 21,
    "config_spot12": 22,
    "config_spot13": 23,
    "config_spot14": 24,
    "config_spot15": 25,
    "config_spot16": 26,
    "config_spot17": 27,
    "config_spot18": 14,
    "config_spot19": 15,
    "config_spot20": 2,
    "config_spot21": 3,
    "config_spot22": 10,
    "config_spot23": 11,
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