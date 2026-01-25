import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

# ---- Setup all GPIO 1–27 as outputs ----
for pin in range(1, 28):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# ---- PIN 1 ----
def pin1_on():
    GPIO.output(1, GPIO.HIGH)

def pin1_off():
    GPIO.output(1, GPIO.LOW)


# ---- PIN 2 ----
def pin2_on():
    GPIO.output(2, GPIO.HIGH)

def pin2_off():
    GPIO.output(2, GPIO.LOW)


# ---- PIN 3 ----
def pin3_on():
    GPIO.output(3, GPIO.HIGH)

def pin3_off():
    GPIO.output(3, GPIO.LOW)


# ---- PIN 4 ----
def pin4_on():
    GPIO.output(4, GPIO.HIGH)

def pin4_off():
    GPIO.output(4, GPIO.LOW)


# ---- PIN 5 ----
def pin5_on():
    GPIO.output(5, GPIO.HIGH)

def pin5_off():
    GPIO.output(5, GPIO.LOW)


# ---- PIN 6 ----
def pin6_on():
    GPIO.output(6, GPIO.HIGH)

def pin6_off():
    GPIO.output(6, GPIO.LOW)


# ---- PIN 7 ----
def pin7_on():
    GPIO.output(7, GPIO.HIGH)

def pin7_off():
    GPIO.output(7, GPIO.LOW)


# ---- PIN 8 ----
def pin8_on():
    GPIO.output(8, GPIO.HIGH)

def pin8_off():
    GPIO.output(8, GPIO.LOW)


# ---- PIN 9 ----
def pin9_on():
    GPIO.output(9, GPIO.HIGH)

def pin9_off():
    GPIO.output(9, GPIO.LOW)


# ---- PIN 10 ----
def pin10_on():
    GPIO.output(10, GPIO.HIGH)

def pin10_off():
    GPIO.output(10, GPIO.LOW)


# ---- PIN 11 ----
def pin11_on():
    GPIO.output(11, GPIO.HIGH)

def pin11_off():
    GPIO.output(11, GPIO.LOW)


# ---- PIN 12 ----
def pin12_on():
    GPIO.output(12, GPIO.HIGH)

def pin12_off():
    GPIO.output(12, GPIO.LOW)


# ---- PIN 13 ----
def pin13_on():
    GPIO.output(13, GPIO.HIGH)

def pin13_off():
    GPIO.output(13, GPIO.LOW)


# ---- PIN 14 ----
def pin14_on():
    GPIO.output(14, GPIO.HIGH)

def pin14_off():
    GPIO.output(14, GPIO.LOW)


# ---- PIN 15 ----
def pin15_on():
    GPIO.output(15, GPIO.HIGH)

def pin15_off():
    GPIO.output(15, GPIO.LOW)


# ---- PIN 16 ----
def pin16_on():
    GPIO.output(16, GPIO.HIGH)

def pin16_off():
    GPIO.output(16, GPIO.LOW)


# ---- PIN 17 ----
def pin17_on():
    GPIO.output(17, GPIO.HIGH)

def pin17_off():
    GPIO.output(17, GPIO.LOW)


# ---- PIN 18 ----
def pin18_on():
    GPIO.output(18, GPIO.HIGH)

def pin18_off():
    GPIO.output(18, GPIO.LOW)


# ---- PIN 19 ----
def pin19_on():
    GPIO.output(19, GPIO.HIGH)

def pin19_off():
    GPIO.output(19, GPIO.LOW)


# ---- PIN 20 ----
def pin20_on():
    GPIO.output(20, GPIO.HIGH)

def pin20_off():
    GPIO.output(20, GPIO.LOW)


# ---- PIN 21 ----
def pin21_on():
    GPIO.output(21, GPIO.HIGH)

def pin21_off():
    GPIO.output(21, GPIO.LOW)


# ---- PIN 22 ----
def pin22_on():
    GPIO.output(22, GPIO.HIGH)

def pin22_off():
    GPIO.output(22, GPIO.LOW)


# ---- PIN 23 ----
def pin23_on():
    GPIO.output(23, GPIO.HIGH)

def pin23_off():
    GPIO.output(23, GPIO.LOW)


# ---- PIN 24 ----
def pin24_on():
    GPIO.output(24, GPIO.HIGH)

def pin24_off():
    GPIO.output(24, GPIO.LOW)


# ---- PIN 25 ----
def pin25_on():
    GPIO.output(25, GPIO.HIGH)

def pin25_off():
    GPIO.output(25, GPIO.LOW)


# ---- PIN 26 ----
def pin26_on():
    GPIO.output(26, GPIO.HIGH)

def pin26_off():
    GPIO.output(26, GPIO.LOW)


# ---- PIN 27 ----
def pin27_on():
    GPIO.output(27, GPIO.HIGH)

def pin27_off():
    GPIO.output(27, GPIO.LOW)


# ---- CLEANUP ----
def cleanup():
    GPIO.cleanup()