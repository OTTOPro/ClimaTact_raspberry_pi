from flask import Flask, render_template, request, jsonify
import RPi.GPIO as GPIO
import time
import dht11
import sqlite3
import threading
import http.client, urllib.parse

app = Flask(__name__, static_folder='templates/static')

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

fire_status = "Aucun feu detecté"
vibration_status = "Aucune vibration detecté"
rain_status = "Aucune pluie detecté"
humidity_status = "Humidité et temperature normales"


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(rouge, GPIO.OUT)
GPIO.setup(Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VibratePin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(buzzer, GPIO.OUT)
GPIO.setup(vert, GPIO.OUT)
GPIO.setup(bleue, GPIO.OUT)
GPIO.setup(DO, GPIO.IN)




def check_pin(pin):
    correct_pin = "1234"
    return pin == correct_pin


def initialize():
    global status

    entered_pin = ask_for_pin()

    if not check_pin(entered_pin):
        print("Incorrect PIN. Exiting the program.")
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
    global rain_status
    tmp = GPIO.input(DO)
    if tmp != status:
        Print(tmp)
        status = tmp
        rain_status = "Ca pleue! Prenez les precautions necessaires"
        for _ in range(5):  
            set_leds((1, 1, 0))
            time.sleep(0.2)  
            set_leds((0, 0, 0))
            time.sleep(0.2)
        time.sleep(5)
        rain_status = "Aucune pluie detecté"
        time.sleep(1)



def set_leds(led):
    l, e, d = led

    GPIO.output(rouge, GPIO.HIGH if l > 0 else GPIO.LOW)
    GPIO.output(vert, GPIO.HIGH if e > 0 else GPIO.LOW)
    GPIO.output(bleue, GPIO.HIGH if d > 0 else GPIO.LOW)


def alert(x):
    global fire_detected
    global sound_detected
    global fire_status
    global vibration_status
    if GPIO.input(Pin) == GPIO.LOW and not fire_detected:
        for _ in range(5):  
            set_leds((0, 1, 1))
            GPIO.output(buzzer, GPIO.LOW)
            fire_status = "Feu detecté! Prenez les precautions necessaires."
            time.sleep(0.2)  # Durée d'allumage
            set_leds((0, 0, 0))
            fire_status = "Feu detecté! Faites Vite!!"
            GPIO.output(buzzer, GPIO.HIGH)
            time.sleep(0.2)  # Durée d'extinction
        fire_detected = True
        print('')
        print('\033[31m  **************** \033[0m')
        print("\033[31m  *Alerte au feu!* \033[0m")
        print('\033[31m  **************** \033[0m')
        print('')
    
    elif GPIO.input(Pin) == GPIO.HIGH and fire_detected:
        fire_status = "Aucun feu detecté"
        fire_detected = False
        set_leds((0, 0, 0))

    if GPIO.input(VibratePin) == GPIO.LOW and not sound_detected:
        for _ in range(5):  # Nombre de clignotements (ajustez selon vos besoins)
            print("Tremblement de Terre détécté. A COUVERT !!!")
            vibration_status = "Tremblement de Terre détécté. A COUVERT !!!"
            set_leds((0, 1, 0))
            GPIO.output(buzzer, GPIO.LOW)
            time.sleep(0.2)  # Durée d'allumage
            set_leds((0, 0, 0))
            GPIO.output(buzzer, GPIO.HIGH)
            time.sleep(0.2)  # Durée d'extinction
        sound_detected = True
    elif GPIO.input(VibratePin) == GPIO.HIGH:
        sound_detected = False
        vibration_status = "Aucune vibration detecté"
        set_leds((0, 0, 0))


def temp_db():
    result = instance.read()
    global humidity_status
    if result.is_valid():
        try:
            conn_temp = sqlite3.connect('temperature.db')
            c_temp = conn_temp.cursor()

            print("Temp: %d C" % result.temperature + ' ' + "Humid: %d %%" % result.humidity)
            temperature = result.temperature
            humidity = result.humidity
            humidity_status = "Humidité et temperature normales"
            date = time.strftime("%Y-%m-%d")
            t = time.strftime("%H:%M:%S")
            c_temp.execute("INSERT INTO dhtsensor(temperature, humidity, Date, Time) VALUES(?,?,?,?)", (temperature, humidity, date, t))
            conn_temp.commit()
            if humidity > 31 or temperature > 32:
                time.sleep(2)
                print("check temperature or humidity!!")
                for _ in range(5):
                    set_leds((0, 0, 1))
                    humidity_status = "Anomalie de temperature ou d'humidité!!Prenez les precautions necessaires."
                    GPIO.output(buzzer, GPIO.LOW)
                    time.sleep(0.2)  # Durée d'allumage
                    set_leds((0, 0, 0))
                    GPIO.output(buzzer, GPIO.HIGH)
                    time.sleep(0.2)

        except Exception as e:
            print(f"Error in temp_db: {str(e)}")
        finally:
            conn_temp.close()
    time.sleep(5)


def temph():
	temperature = 0
	humidity = 0
	result = instance.read()
	if result.is_valid():
		temperature = result.temperature
		humidity = result.humidity
	params = urllib.parse.urlencode({'field1': temperature,'field2': humidity,'key':'JECPDX428Q36R7WX'})
	headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
	conn = http.client.HTTPConnection("api.thingspeak.com:80")
	
	try:
		conn.request("POST", "/update", params, headers)
		response = conn.getresponse()
		print("Temperature: %d C" % result.temperature + ' ' + "Humidité: %d %%" % result. humidity)
		data = response.read()
		conn.close()
	except:
		print ("connection failed")	


def loop():
    GPIO.add_event_detect(Pin, GPIO.BOTH, callback=alert)
    GPIO.add_event_detect(VibratePin, GPIO.BOTH, callback=alert)
    GPIO.add_event_detect(DO, GPIO.BOTH, callback=pluie)
    while True:
        temp_db()
        temph()
        pass
        time.sleep(1)


@app.route('/')
def index():
    return render_template('initialize.html')


@app.route('/check_pin', methods=['POST'])
def check_pin_route():
    entered_pin = request.form['pin']
    if check_pin(entered_pin):
        set_leds((1, 0, 1))
        time.sleep(3)
        set_leds((0, 0, 0))
        return "PIN Correct!"
    else:
        set_leds((0, 1, 1))
        time.sleep(3)
        set_leds((0, 0, 0))
        return "PIN Incorrect!"


@app.route('/dht_data')
def get_dht_data():
    try:
        conn = sqlite3.connect('temperature.db')
        c = conn.cursor()

        sql_query = "SELECT * FROM dhtsensor ORDER BY Date DESC, Time DESC LIMIT 5"
        print(f"Executing SQL query: {sql_query}")
        c.execute(sql_query)
        dht_data = c.fetchall()

        conn.close()

        return jsonify(dht_data)
    except Exception as e:
        print(f"Error fetching DHT data: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/principal')
def principale_page():
    return render_template('index.html', fire_status=fire_status, vibration_status=vibration_status, rain_status=rain_status, humidity_status=humidity_status)

@app.route('/sensor_states')
def get_sensor_states():
    return jsonify({
        "fire_status": fire_status,
        "vibration_status": vibration_status,
        "rain_status": rain_status,
        "humidity_status": humidity_status
    })


def applicationweb():
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    try:

        loop_thread = threading.Thread(target=loop, daemon=True)
        loop_thread.start()
        loop_app = threading.Thread(target=applicationweb, daemon=True)
        loop_app.start()
        


    except KeyboardInterrupt:
        GPIO.cleanup()

