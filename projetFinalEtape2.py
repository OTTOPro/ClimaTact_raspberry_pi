import RPi.GPIO as GPIO
import time
import dht11
import sqlite3
import PCF8591 as ADC

Pin = 4
rouge = 17    
vert = 22    
bleue = 27
DO = 12
VibratePin = 18
buzzer = 24
status = 1
fire_detected = False
sound_detected = False
conn = sqlite3.connect('temperature.db')
c = conn.cursor()
instance = dht11.DHT11(pin=23)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(rouge, GPIO.OUT)
GPIO.setup(Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VibratePin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(buzzer, GPIO.OUT)
GPIO.setup(vert, GPIO.OUT)
GPIO.setup(bleue, GPIO.OUT)
ADC.setup(0x48)
GPIO.setup(DO, GPIO.IN)


def ask_for_pin():
    user_pin = input("Entrez le code PIN : ")
    return user_pin

def check_pin(pin):
    correct_pin = "1234"  
    return pin == correct_pin

def initialize():
    global status

    entered_pin = ask_for_pin()

    if not check_pin(entered_pin):
        print("Code PIN incorrect. Le programme s'arrête.")
        GPIO.cleanup()
        exit()

def Print(x):
    if x == 1:
        print('')
        print('   ***************')
        print('   * Not raining *')
        print('   ***************')
        print('')
    if x == 0:
        print('')
        print('   *************')
        print('   * Raining!! *')
        print('   *************')
        print('')


def pluie(x):
    global status
    tmp = GPIO.input(DO)
    if tmp != status:
        Print(tmp)
        status = tmp
        for _ in range(5):  # Nombre de clignotements (ajustez selon vos besoins)
            set_leds((1, 1, 0))
            time.sleep(0.2)  # Durée d'allumage
            set_leds((0, 0, 0))
            time.sleep(0.2)
        time.sleep(1)


def set_leds(led):
    l, e, d = led
    
    # Etat de la LED rouge selon la valeur donnée en paramètre pour l
    GPIO.output(rouge, GPIO.HIGH if l > 0 else GPIO.LOW)

    # Etat de la LED verte selon la valeur donnée en paramètre pour e
    GPIO.output(vert, GPIO.HIGH if e > 0 else GPIO.LOW)

    # Etat de la LED bleue selon la valeur donnée en paramètre pour d
    GPIO.output(bleue, GPIO.HIGH if d > 0 else GPIO.LOW)


def alert(x):
    global fire_detected
    global sound_detected
    if GPIO.input(Pin) == GPIO.LOW and not fire_detected:
        for _ in range(5):  # Nombre de clignotements (ajustez selon vos besoins)
            set_leds((0, 1, 1))
            GPIO.output(buzzer, GPIO.LOW)
            time.sleep(0.2)  # Durée d'allumage
            set_leds((0, 0, 0))
            GPIO.output(buzzer, GPIO.HIGH)
            time.sleep(0.2)  # Durée d'extinction
        fire_detected = True
        print('')
        print('\033[31m  **************** \033[0m')
        print("\033[31m  *Alerte au feu!* \033[0m")
        print('\033[31m  **************** \033[0m')
        print('')
    elif GPIO.input(Pin) == GPIO.HIGH:
        fire_detected = False
        set_leds((0, 0, 0))

    if GPIO.input(VibratePin) == GPIO.LOW and not sound_detected:
        for _ in range(5):  # Nombre de clignotements (ajustez selon vos besoins)
            print("Tremblement de Terre détécté. A COUVERT !!!")
            set_leds((0, 1, 0))
            GPIO.output(buzzer, GPIO.LOW)
            time.sleep(0.2)  # Durée d'allumage
            set_leds((0, 0, 0))
            GPIO.output(buzzer, GPIO.HIGH)
            time.sleep(0.2)  # Durée d'extinction
        sound_detected = True
    elif GPIO.input(VibratePin) == GPIO.HIGH:
        sound_detected = False
        set_leds((0, 0, 0))


def temp_db():
    result = instance.read()
    if result.is_valid():
        print("Temp: %d C" % result.temperature + ' ' + "Humid: %d %%" % result.humidity)
        temperature = result.temperature
        humidity = result.humidity
        if humidity > 25 or temperature > 32:
            print("check temperature or humidity!!")
            for _ in range(5):
                set_leds((0, 0, 1))
                GPIO.output(buzzer, GPIO.LOW)
                time.sleep(0.2)  # Durée d'allumage
                set_leds((0, 0, 0))
                GPIO.output(buzzer, GPIO.HIGH)
                time.sleep(0.2)
        date = time.strftime("%Y-%m-%d")
        t = time.strftime("%H:%M:%S")
        c.execute("INSERT INTO dhtsensor(temperature, humidity, Date, Time) VALUES(?,?,?,?)", (temperature, humidity, date, t))
        conn.commit()
    time.sleep(15)


def loop():
    GPIO.add_event_detect(Pin, GPIO.BOTH, callback=alert)
    GPIO.add_event_detect(VibratePin, GPIO.BOTH, callback=alert)
    GPIO.add_event_detect(DO, GPIO.BOTH, callback=pluie)
    while True:
        temp_db()
        pass

try:  
    initialize()
    set_leds((1, 0, 1))
    time.sleep(3)
    loop()
except KeyboardInterrupt:
    GPIO.cleanup()
