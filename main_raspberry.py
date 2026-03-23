import subprocess
import socket
import time
import atexit
from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

agent_process = None

def przygotuj_bluetooth():
    global agent_process
    print("Konfiguracja modułu Bluetooth...")

    # 1. Włączenie radia
    subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=False)
    subprocess.run(["bluetoothctl", "power", "on"], check=False)

    # 2. Wyłączenie domyślnego agenta (tego z PINem)
    subprocess.run(["bluetoothctl", "agent", "off"], stdout=subprocess.DEVNULL)

    # 3. Uruchomienie agenta NoInputNoOutput (bez PINu) w tle
    subprocess.run(["sudo", "killall", "bt-agent"], stderr=subprocess.DEVNULL)
    agent_process = subprocess.Popen(["bt-agent", "-c", "NoInputNoOutput"])

    # 4. Włączenie widoczności i możliwości parowania
    subprocess.run(["bluetoothctl", "discoverable", "on"], check=False)
    subprocess.run(["bluetoothctl", "pairable", "on"], check=False)
    print("Bluetooth jest teraz WIDOCZNY. Możesz parować telefon bez PINu!")

def ukryj_bluetooth():
    global agent_process
    print("\nUkrywanie Bluetooth i zamykanie agenta...")
    subprocess.run(["bluetoothctl", "discoverable", "off"], check=False)
    subprocess.run(["bluetoothctl", "pairable", "off"], check=False)
    if agent_process:
        agent_process.terminate()

# Zarejestrowanie funkcji, która wykona się ZAWSZE przy zamykaniu skryptu
atexit.register(ukryj_bluetooth)


# Inicjalizacja czujnika MPU
mpu = MPU9250(
    address_ak=AK8963_ADDRESS,
    address_mpu_master=MPU9050_ADDRESS_68,
    bus=1
)
mpu.configure()

# Bluetooth
przygotuj_bluetooth()

# Otwarcie socketa Bluetooth
server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
port = 1
server_sock.bind(("00:00:00:00:00:00", port))
server_sock.listen(1)

try:
    print("Czekam na połączenie z telefonu...")
    #Połączenie i ukrycie Bluetootha przed innymi
    client_sock, address = server_sock.accept()
    print(f"Połączono z: {address[0]}")
    ukryj_bluetooth()

    # Wysyłanie danych w pętli
    while True:
        accel = mpu.readAccelerometerMaster()
        wiadomosc = f"Akcelerometr X: {accel[0]:.2f} Y: {accel[1]:.2f} Z: {accel[2]:.2f}\n"

        client_sock.send(wiadomosc.encode("utf-8"))
        time.sleep(0.5)

except OSError:
    print("Klient się rozłączył.")
except KeyboardInterrupt:
    print("\nZakończono przez użytkownika.")
finally:
    server_sock.close()
