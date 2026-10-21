#!/usr/bin/env python

import signal
import time
import RPi.GPIO as GPIO
from pirc522 import RFID

# Configuration des GPIO en mode BOARD
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Configuration de l'alarme / buzzer sur la broche 13
ALARM_PIN = 33
GPIO.setup(ALARM_PIN, GPIO.OUT)
GPIO.output(ALARM_PIN, GPIO.LOW)  # Alarme éteinte au démarrage

run = True

# Initialisation du lecteur RFID en mode BOARD (pin_rst=22 pour le GPIO 25 BCM)
rdr = RFID(pin_mode=GPIO.BOARD, pin_rst=22, pin_irq=None)
util = rdr.util()
util.debug = True

def end_read(signal, frame):
    global run
    print("\nCtrl+C captured, ending read.")
    run = False
    rdr.cleanup()
    GPIO.cleanup()

signal.signal(signal.SIGINT, end_read)

print("Starting (polling mode - BOARD mode with buzzer)")
while run:
    (error, data) = rdr.request()
    if not error:
        print("\nDetected: " + format(data, "02x"))

        (error, uid) = rdr.anticoll()
        if not error:
            print("Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))

            # Le buzzer sonne pendant 0,4 seconde lors de la lecture d'une carte
            GPIO.output(ALARM_PIN, GPIO.HIGH)
            time.sleep(0.4)
            GPIO.output(ALARM_PIN, GPIO.LOW)

            print("Setting tag")
            util.set_tag(uid)
            print("\nAuthorizing")
            util.auth(rdr.auth_a, [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

            # Définition du bloc cible
            block_to_check = 10

            # Vérification : Un bloc trailer ("remorque") se trouve toujours à la fin d'un secteur (bloc % 4 == 3)
            if block_to_check % 4 == 3:
                print(f"\n[ATTENTION] Le bloc {block_to_check} est une remorque (Sector Trailer) ! Écrire dedans risquerait de briser/bloquer la carte.")
            else:
                print(f"\n[OK] Le bloc {block_to_check} n'est pas une remorque. Lecture sécurisée...")
                util.read_out(block_to_check)

            # Fin de l'authentification pour ce cycle
            util.deauth()

            time.sleep(1)
    else:
        # Petite pause pour éviter de surcharger le processeur
        time.sleep(0.1)