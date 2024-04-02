import RPi.GPIO as GPIO
import time

Pin = 4
rouge = 17	
vert = 22	
bleue = 27
VibratePin = 18
fire_detected = False
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(rouge, GPIO.OUT)
GPIO.setup(Pin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(VibratePin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


GPIO.setmode(GPIO.BCM)

GPIO.setup(rouge, GPIO.OUT)
GPIO.setup(vert, GPIO.OUT)
GPIO.setup(bleue, GPIO.OUT)

def set_leds(led):
    
    l, e, d = led
    
    # Etat de la led rouge selon la valeur donner en parametre pour l
    GPIO.output(rouge, GPIO.HIGH if l > 0 else GPIO.LOW)

    # Etat de la led verte selon la valeur donner en parametre pour e
    GPIO.output(vert, GPIO.HIGH if e > 0 else GPIO.LOW)

    # Etat de la led bleue selon la valeur donner en parametre pour d
    GPIO.output(bleue, GPIO.HIGH if d > 0 else GPIO.LOW)

    
    
def alert(x):
    global fire_detected
    if GPIO.input(Pin) == GPIO.LOW:
        if not fire_detected:
            set_leds((0, 1, 1))
            print('')
            print('\033[31m  **************** \033[0m')
            print("\033[31m  *Alerte au feu!* \033[0m")
            print('\033[31m  **************** \033[0m')
            print('')
    else:
        fire_detected = False
        set_leds((1, 0, 1))
        
def detect_vibration(c):  
    if GPIO.input(VibratePin) == 0:
        print("Vibration detected!")
        set_leds((0, 1, 1))
              


def loop():
    set_leds((1, 0, 1))
    GPIO.add_event_detect(Pin,GPIO.BOTH,callback=alert)
    GPIO.add_event_detect(VibratePin,GPIO.FALLING,callback=detect_vibration)
    while True:
        pass


try:
    loop()
except KeyboardInterrupt:
    GPIO.cleanup()

