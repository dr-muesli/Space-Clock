# HAXKO SPACE-UHR // Version für Workshop
#
#
# https://haxko.space/
#
# https://woof.tech/@dr_muesli
#
__author__ = "Magic Mystery Muesli"
__contact__ = "https://woof.tech/@dr_muesli"
__version__ = 20260501
__license__ = "AGPLv3"

from machine import Pin
from time import sleep
from neopixel import NeoPixel
import urandom, random, time
import network, ntptime
import machine, os


# Variablen festlegen:
Farbmodus = 0

m01 = [0, 1, 2, 15, 16, 17, 18, 19, 20]
m02 = [3, 4, 13, 14, 21, 22]
h01 = [5, 6, 7, 10, 11, 12, 23, 24, 25]
h02 = [8, 9, 26]

ofs = 9     # =offset für NeoPixel-Adresse (=0 für 9x3 / =9 für 9x5)

Zeit = "0000"
boot = True
logoakt = False  # (nicht ändern)
synchronisierung = False  # (nicht ändern)
low_light = True
pixeltest = False
WIDTH = 9
HEIGHT = 3


# Konfiguration je nach ESP Modell:
print(os.uname())
info = os.uname().machine.lower()
if "c3" in info:
    print("ESP32-C3-SuperMini erkannt")
    np = NeoPixel(Pin(4), 27)
    taster = Pin(3, Pin.IN, Pin.PULL_DOWN)
elif "s2" in info:
    print("ESP32-S2-mini erkannt")
    np = NeoPixel(Pin(16), 45)       # =27 NP bei 9x3 / =45 NP bei 9x5  (Pin gegebenfalls anpassen)
    taster = Pin(0, Pin.IN, Pin.PULL_DOWN)   # Optionaler Tasteranschluss gegen 3,3V (Pin gegebenfalls anpassen)

    
# Boot-LED Anzeige:
def boot_led(pos, status, sleeping):
    if boot:
        if status == 2:
            np[ofs + pos] = (60, 60, 0)  # gelb
        elif status == 1:
            np[ofs + pos] = (0, 100, 0)  # grün
        else:
            np[ofs + pos] = (100, 0, 0)  # rot
        np.write()
        sleep(sleeping)

print("Hi !")
for x in range(26): np[ofs + x] = (0, 0, 0)
boot_led(0, 1, 0)

sleep(1)  # Sicherheitswartezeit zum reseten bei Fehlern



#---Abschnitt für WLAN und NTP Zeitabfrage (inkl. So/Wi-Zeitumrechnung):

wlan = network.WLAN(network.STA_IF)


#   ! WLAN Zugangsdaten sind jetzt extern hinterlegt auf wlan_data.py
from wlan_data import WLAN_NETZE


def wlan_verbinden():
    for ssid, pw in WLAN_NETZE:
        wlan.active(False)
        boot_led(1, 2, 1.5)
        wlan.active(True)
        print("Versuche Verbindung zu:", ssid)
        wlan.connect(ssid, pw)

        for _ in range(10):  # 5 sekunden warten
            if wlan.isconnected():
                print("Verbunden mit", ssid)
                print("IP-Adresse:", wlan.ifconfig()[0])
                
                # nur aktuelle WLAN verbindung merken für schnellere Syncronisierung:
                WLAN_NETZE[:] = [(ssid, pw)]
                
                boot_led(1, 1, 0)
                return True
            sleep(0.5)

        print("Konnte nicht verbinden:", ssid)
        boot_led(1, 0, 0.2)

    print("Kein WLAN gefunden.")
    return False


def get_dst_offset(year, month, day, hour):

    # Letzter Sonntag im März (beginn Sommerzeit)
    march_last_sunday = max(
        d for d in range(25, 32)
        if time.localtime(time.mktime((year, 3, d, 0, 0, 0, 0, 0)))[6] == 6
    )
    # Letzter Sonntag im Oktober (ende Sommerzeit)
    oct_last_sunday = max(
        d for d in range(25, 32)
        if time.localtime(time.mktime((year, 10, d, 0, 0, 0, 0, 0)))[6] == 6
    )

    # Sommerzeit aktiv? (umstellung basiert auf UTC Zeit!)
    if (month > 3 and month < 10) or \
       (month == 3 and (day > march_last_sunday or (day == march_last_sunday and hour >= 1))) or \
       (month == 10 and (day < oct_last_sunday or (day == oct_last_sunday and hour < 1))):
        return 2  # MESZ (Sommerzeit)
    else:
        return 1  # MEZ (Winterzeit / Normalzeit)


def set_local_time():
    try:
        boot_led(2, 2, 0)
        ntptime.host = "ptbtime3.ptb.de" 	# alternativ: "europe.pool.ntp.org"
        ntptime.settime() 	# RTC auf UTC stellen
        print("NTP Zeit geholt (UTC).")
        
        boot_led(2, 1, 0)
    except Exception as e:
        print("Konnte NTP-Zeit nicht holen:", e)
        
        boot_led(2, 0, 0)
        return False

    # Aktuelle UTC-Zeit
    t = time.localtime()
    year, month, day, hour, minute, second, weekday, yearday = t

    offset = get_dst_offset(year, month, day, hour)

    # Zeitstempel + Offset (lokale Zeit berechnen)
    ts = time.mktime((year, month, day, hour, minute, second, weekday, yearday))
    ts += offset * 3600
    lt = time.localtime(ts)

    # RTC direkt mit lokaler Zeit setzen
    rtc = machine.RTC()
    rtc.datetime((lt[0], lt[1], lt[2], lt[6]+1, lt[3], lt[4], lt[5], 0))
    print("RTC auf deutsche Zeit gesetzt:", rtc.datetime())
    return True



if time.localtime()[0] > 2010:
    print("ESP-Zeit aktuell. Direktstart ohne WLAN und NTP verbindung.")
else:
    if wlan_verbinden():    
        sleep(2.5)
        for x in range(10):
            if set_local_time():
                print("Juhu! Hat alles funktioniert!")
                break
            elif x == 9:
                print("Konnte keine NTP Zeit holen")
            else:
                sleep(2)
    else:
        print("Keine WLAN-Verbindung, keine Zeitabfrage möglich. :(")

wlan.active(False) #WLAN deaktivieren
boot_led(3, 1, 0.5)
boot = False



#---Snake Animation:

# Zickzack-Mapping dank toller NeoPixel anordnung xD :
def idx(x, y):
    if y % 2 == 0:
        return y * WIDTH + (WIDTH - 1 - x)
    else:
        return y * WIDTH + x

def reset_game():
    snake = [(4, 1)]
    dx, dy = 1, 0

    # Ersten Apfel auf freies Feld setzen:
    free_fields = [(x,y) for x in range(WIDTH) for y in range(HEIGHT) if (x,y) not in snake]
    apple = random.choice(free_fields)
    return snake, dx, dy, apple

def snake(Apples = 12):
    global Farbmodus
    snake, dx, dy, apple = reset_game()

    while True:
        head_x, head_y = snake[0]

        # Wunschrichtung Apfel
        preferred = []
        if head_x < apple[0]: preferred.append((1,0))
        if head_x > apple[0]: preferred.append((-1,0))
        if head_y < apple[1]: preferred.append((0,1))
        if head_y > apple[1]: preferred.append((0,-1))
        if not preferred: preferred = [(dx,dy)]

        # Ausweichrichtungen hinzufügen:
        all_moves = [(1,0), (-1,0), (0,1), (0,-1)]
        for m in all_moves:
            if m not in preferred:
                preferred.append(m)

        # Richtung wählen, Kollision vermeiden:
        chosen = None
        for mx,my in preferred:
            nx = max(0, min(WIDTH-1, head_x + mx))
            ny = max(0, min(HEIGHT-1, head_y + my))
            if (nx, ny) not in snake:
                chosen = (mx,my)
                break
        if chosen is None:
            chosen = preferred[0]  # letzte Notlösung

        dx, dy = chosen

        # Kopf bewegen:
        new_x = max(0, min(WIDTH-1, head_x + dx))
        new_y = max(0, min(HEIGHT-1, head_y + dy))
        new_head = (new_x, new_y)

        # Selbstkollision / GameOver:
        if new_head in snake:
            print("Gegessene Äpfel:", len(snake) - 1)
            sleep(1)
            snake, dx, dy, apple = reset_game()
            continue

        snake.insert(0, new_head)

        # Leckeren NeoPixel-Apfel gegessen?:
        if new_head == apple:
            # Einen neuen Apfel auf ein freies Feld setzen:
            free_fields = [(x,y) for x in range(WIDTH) for y in range(HEIGHT) if (x,y) not in snake]
            apple = random.choice(free_fields)
        else:
            snake.pop()
            
        # Rendern/Pixel setzen:
        for i in range(27): np[ofs + i] = (0,0,0)

        ax, ay = apple                      # Apfel
        if len(snake) <= Apples:
            np[ofs + idx(ax, ay)] = (110,8,8) if len(snake)<Apples else (100,100,8)

        for n,(sx,sy) in enumerate(snake):  # Schlange
            np[ofs + idx(sx,sy)] = (8,200,8) if n==0 else (3,70,3)

        np.write()
        
        
        # Letzten/Goldenen Apfel gegessen? / Spiel Gewonnen:
        if len(snake) > Apples:
            print(f"Alle {Apples} Äpfel gegessen")
            sleep(1)
            snake, dx, dy, apple = reset_game()
            if not Farbmodus == 2: break
        

        # Geschwindigkeit / Timer und Tasterabfrage zum Umschalten:
        for _ in range(2):
            sleep(0.09)
            if Farbmodus == 3 and taster.value() == 1:
                Farbmodus = 0
                sleep(0.5)
                return


#---Hauptprogramm Space-Uhr:

# Zufallsgenerator
def rnd(lst, k):
    k = int(k)
    k = min(k, len(lst))  #(nicht mehr ziehen als vorhanden)
    result = []
    pool = lst[:]
    for _ in range(k):
        i = urandom.getrandbits(8) % len(pool)
        result.append(pool.pop(i))
    return result

def modus_haxko():
    for i in range(11):
        
        if i == 1:
            for x in [6, 8, 9, 10, 11, 24, 26]:  #H
                np[ofs + x] = (134, 172, 172)
            np.write()
            sleep(0.3)
        elif i == 3:
            for x in [5, 7, 10, 12, 24]:  #A
                np[ofs + x] = (134, 172, 172)
            np.write()
            sleep(0.3)
        elif i == 5:
            for x in [3, 5, 13, 21, 23]:  #X
                np[ofs + x] = (180, 70, 0)
            np.write()
            sleep(0.3)
        elif i == 7:
            for x in [1, 3, 14, 15, 19, 21]:  #K
                np[ofs + x] = (134, 172, 172)
            np.write()
            sleep(0.3)
        elif i == 9:
            for x in [1, 15, 17, 19]:  #O
                np[ofs + x] = (134, 172, 172)
            np.write()
            sleep(0.3)
        else:
            for x in range(27):
                np[ofs + x] = (100, 100, 100)
            np.write()
            sleep(0.1)

        
        for x in range(27): np[ofs + x] = (0, 0, 0)
        np.write()
        sleep(0.1)
        
        
def modus_rauschen():
    for _ in range(150):
        for x in range(27):
            for z in rnd([0, 1, 2], 1): y =  z * 40
            np[ofs + x] = (y, y, y)
        np.write()
        sleep(0.02)
        
        
def modus_balken(bunt=False):
    for y in range(27):
        np[ofs + y] = (0, 0, 0)
    
    for _ in range(4):
        for i in range(16):
            if i > 8:
                x = 8 - (i - 8)
            else:
                x = i
            
            z = 0
            if bunt == True: z = x + 1
            r = [100, 100, 100, 100, 0, 0, 0, 50, 100, 100]
            g = [100, 0, 50, 100, 100, 50, 0, 0, 25, 100]
            b = [100, 0, 0, 0, 0, 100, 100, 100, 75, 100]
            
            np[ofs + (8 - x)] = (r[z], g[z], b[z])
            np[ofs + (9 + x)] = (r[z], g[z], b[z])
            np[ofs + (26 - x)] = (r[z], g[z], b[z])
            np.write()
            
            # Reset + Schatten für nächste Runde vorbereiten:
            for y in range(27): np[ofs + y] = (0, 0, 0)
                
            np[ofs + (8 - x)] = (r[z] // 5, g[z] // 5, b[z] // 5)
            np[ofs + (9 + x)] = (r[z] // 5, g[z] // 5, b[z] // 5)
            np[ofs + (26 - x)] = (r[z] // 5, g[z] // 5, b[z] // 5)
            
            sleep(0.07)
            
if pixeltest:
    for x in range(len(np)): np[x] = (0,0,0)
    for x in range(len(np)):
        if low_light:
            np[x] = (90,0,0)
        else:
            np[x] = (200,0,0)
        np.write()
        sleep(0.03)
    for x in range(len(np)): np[x] = (0,0,0)
        
        
while True:
    
    #Zeitabfrage mit führender 0 als String
    akt_Zeit = time.localtime()
    stunden = str(akt_Zeit[3])
    minuten = str(akt_Zeit[4])
    if len(stunden) == 1: stunden = "0" + stunden
    if len(minuten) == 1: minuten = "0" + minuten
    if akt_Zeit[0] > 2020:
        Zeit = stunden + minuten
    else:
        Zeit = "1337"
            
    print("Aktuelle Zeit: " + Zeit)
    zeitwerte = [int(c) for c in Zeit]


    if Farbmodus == 0 and low_light:
        # alle LEDs zurücksetzen (gedimmt, aus)
        for x in m01: np[ofs + x] = (7, 1, 1)
        for x in m02: np[ofs + x] = (1, 1, 4)
        for x in h01: np[ofs + x] = (1, 5, 1)
        for x in h02: np[ofs + x] = (6, 3, 1)
        # Zufalls-LEDs setzen
        for x in rnd(m01, zeitwerte[3]): np[ofs + x] = (90, 10, 10)
        for x in rnd(m02, zeitwerte[2]): np[ofs + x] = (20, 20, 80)
        for x in rnd(h01, zeitwerte[1]): np[ofs + x] = (7, 80, 7)
        for x in rnd(h02, zeitwerte[0]): np[ofs + x] = (70, 70, 6)
        np.write()
    elif Farbmodus == 1 and low_light:
        # alle LEDs zurücksetzen (gedimmt, aus):
        for x in m01: np[ofs + x] = (3, 0, 5)
        for x in m02: np[ofs + x] = (0, 1, 4)
        for x in h01: np[ofs + x] = (3, 0, 5)
        for x in h02: np[ofs + x] = (0, 1, 4)
        # Zufalls-LEDs setzen:
        for x in rnd(m01, zeitwerte[3]): np[ofs + x] = (90, 0, 100)
        for x in rnd(m02, zeitwerte[2]): np[ofs + x] = (0, 60, 80)
        for x in rnd(h01, zeitwerte[1]): np[ofs + x] = (90, 0, 100)
        for x in rnd(h02, zeitwerte[0]): np[ofs + x] = (0, 60, 80)
        np.write()
    elif Farbmodus == 2 and low_light:
        for x in range(9):
            if akt_Zeit[5] & (1 << x):
                np[ofs + x] = (10, 70, 10)
            else:
                np[ofs + x] = (0, 0, 0)
            if akt_Zeit[4] & (1 << x):
                np[ofs + 17 - x] = (10, 10, 70)
            else:
                np[ofs + 17 - x] = (0, 0, 0)
            if akt_Zeit[3] & (1 << x):
                np[ofs + 18 + x] = (70, 10, 10)
            else:
                np[ofs + 18 + x] = (0, 0, 0)
        np.write()
    elif Farbmodus == 0:
        # alle LEDs zurücksetzen (gedimmt, aus)
        for x in m01: np[ofs + x] = (10, 2, 2)
        for x in m02: np[ofs + x] = (2, 2, 6)
        for x in h01: np[ofs + x] = (2, 8, 2)
        for x in h02: np[ofs + x] = (8, 5, 1)
        # Zufalls-LEDs setzen
        for x in rnd(m01, zeitwerte[3]): np[ofs + x] = (200, 20, 20)
        for x in rnd(m02, zeitwerte[2]): np[ofs + x] = (50, 50, 160)
        for x in rnd(h01, zeitwerte[1]): np[ofs + x] = (10, 180, 10)
        for x in rnd(h02, zeitwerte[0]): np[ofs + x] = (200, 180, 10)
        np.write()
    elif Farbmodus == 1:
        # alle LEDs zurücksetzen (gedimmt, aus):
        for x in m01: np[ofs + x] = (3, 0, 5)
        for x in m02: np[ofs + x] = (0, 2, 7)
        for x in h01: np[ofs + x] = (3, 0, 5)
        for x in h02: np[ofs + x] = (0, 2, 7)
        # Zufalls-LEDs setzen:
        for x in rnd(m01, zeitwerte[3]): np[ofs + x] = (180, 0, 200)
        for x in rnd(m02, zeitwerte[2]): np[ofs + x] = (0, 150, 200)
        for x in rnd(h01, zeitwerte[1]): np[ofs + x] = (180, 0, 200)
        for x in rnd(h02, zeitwerte[0]): np[ofs + x] = (0, 150, 200)
        np.write()
    elif Farbmodus == 2:
        for x in range(9):
            if akt_Zeit[5] & (1 << x):
                np[ofs + x] = (10, 180, 10)
            else:
                np[ofs + x] = (0, 0, 0)
            if akt_Zeit[4] & (1 << x):
                np[ofs + 17 - x] = (50, 50, 160)
            else:
                np[ofs + 17 - x] = (0, 0, 0)
            if akt_Zeit[3] & (1 << x):
                np[ofs + 18 + x] = (200, 20, 20)
            else:
                np[ofs + 18 + x] = (0, 0, 0)
        np.write()
    

    
    # Warteschleife 4-sekunden mit tasterabfrage für Animation:
    for x in range(40):
        sleep(0.1)
        if taster.value() == 1:
            sleep(0.2)
            if taster.value() == 1:
                modus_haxko()
                modus_balken(True)
                modus_haxko()
            else:
                Farbmodus += 1
                if Farbmodus > 3: Farbmodus = 0
            break
        elif Farbmodus == 2 and x >= 10:  # Sekundentakt für Binäruhr
            break
        
    
        
    # Erweiterte Animationen unter Farbmodus:
    if Farbmodus == 3: snake()

    # Animation und Zeitsynchronisierung:
    if logoakt == False and Zeit == "0000":
        logoakt = True
        sleep(10)
        modus_rauschen()
        modus_balken()
        modus_haxko()
        modus_balken(True)
        modus_haxko()
        
    elif synchronisierung == False and (Zeit == "0201" or Zeit == "0301" or (akt_Zeit[0] < 2020 and minuten[1] == "5")):
        synchronisierung = True
        wlan_verbinden()
        set_local_time()
        wlan.active(False)
        
    elif minuten[1] == "9":
        logoakt = False
        synchronisierung = False
    