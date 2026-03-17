import time
from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

mpu = MPU9250(
    address_ak=AK8963_ADDRESS, 
    address_mpu_master=MPU9050_ADDRESS_68, 
    bus=1
)

try:
    print("Konfiguracja sensora...")
    mpu.configure()

    print("Odczyt danych (Ctrl+C, aby zakończyć):")
    while True:
        accel = mpu.readAccelerometerMaster()
        gyro = mpu.readGyroscopeMaster()

        print(f"Akcelerometr: {accel} | Żyroskop: {gyro}")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nPrzerwano.")
except Exception as e:
    print(f"\nWystąpił błąd: {e}")