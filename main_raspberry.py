import subprocess
import socket
import time
import atexit
from gpiozero import Button
from signal import pause
from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

# --- KONFIGURACJA PRZYCISKU ---
# Zakładamy, że SIG jest wpięty w GPIO 17 (Pin 11)
PRZYCISK_PIN = 17 
# pull_up=False, bo moduły z VCC zazwyczaj wysyłają sygnał 3.3V po kliknięciu
przycisk = Button(PRZYCISK_PIN, pull_up=False)

agent_process = None
system_uruchomiony = False # Flaga, żeby nie odpalać dwa razy naraz

def przygotuj_bluetooth():
    global agent_process
    print("Konfiguracja modułu Bluetooth...")

    # 1. Włączenie radia
    subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=False)
    subprocess.run(["sudo", "bluetoothctl", "power", "on"], check=False)

    # 2. Wyłączenie domyślnego agenta (tego z PINem)
    subprocess.run(["sudo", "bluetoothctl", "agent", "off"], stdout=subprocess.DEVNULL)

    # 3. Uruchomienie agenta NoInputNoOutput (Tryb JBL)
    subprocess.run(["sudo", "killall", "bt-agent"], stderr=subprocess.DEVNULL)
    agent_process = subprocess.Popen(["sudo", "bt-agent", "-c", "NoInputNoOutput"])
    time.sleep(1)

    # 4. Otwarcie portu SPP
    subprocess.run(["sudo", "chmod", "777", "/var/run/sdp"], check=False)
    subprocess.run(["sudo", "sdptool", "add", "SP"], check=False)

    # 5. Włączenie widoczności
    subprocess.run(["sudo", "bluetoothctl", "discoverable", "on"], check=False)
    subprocess.run(["sudo", "bluetoothctl", "pairable", "on"], check=False)
    print("Bluetooth widoczny! Czekam na połączenie z telefonu...")

def ukryj_bluetooth():
    global agent_process
    print("\nUkrywanie Bluetooth i zamykanie agenta...")
    subprocess.run(["sudo", "bluetoothctl", "discoverable", "off"], check=False)
    subprocess.run(["sudo", "bluetoothctl", "pairable", "off"], check=False)
    if agent_process:
        agent_process.terminate()

atexit.register(ukryj_bluetooth)

# Inicjalizacja czujnika MPU (robimy to raz na początku)
print("Inicjalizacja czujnika MPU...")
mpu = MPU9250(
    address_ak=AK8963_ADDRESS,
    address_mpu_master=MPU9050_ADDRESS_68,
    bus=1
)
mpu.configure()

# --- FUNKCJA URUCHAMIANA PRZYCISKIEM ---
def start_programu():
    global system_uruchomiony
    if system_uruchomiony:
        return # Jeśli już działa, zignoruj kolejne kliknięcia
    
    system_uruchomiony = True
    przygotuj_bluetooth()

    # Otwarcie serwera Bluetooth
    server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    port = 1
    server_sock.bind(("00:00:00:00:00:00", port))
    server_sock.listen(1)

    try:
        client_sock, address = server_sock.accept()
        print(f"Połączono z: {address[0]}")

        ukryj_bluetooth()

        while True:
            accel = mpu.readAccelerometerMaster()
            gyro = mpu.readGyroscopeMaster()
            wiadomosc = f"Akcelerometr: {accel} | Żyroskop: {gyro}\n"
            client_sock.send(wiadomosc.encode("utf-8"))
            time.sleep(0.5)

    except OSError:
        print("Klient się rozłączył.")
    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        server_sock.close()
        system_uruchomiony = False
        print("🛑 System uśpiony. Czekam na przycisk...")

# --- GŁÓWNA PĘTLA ---
print("Program gotowy. Naciśnij przycisk, aby włączyć Bluetooth.")
przycisk.when_pressed = start_programu

# Zatrzymuje skrypt w miejscu, żeby się nie wyłączył
pause()
