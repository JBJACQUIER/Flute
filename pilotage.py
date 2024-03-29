""" Programme qui permet le pilotage des servomoteurs. """
from pyb import Timer, Pin, LED
import time
import ustruct


# Témoin d'accès au fichier.
print('-> pilotage')

LED(1).on()
time.sleep(0.5)
LED(2).on()
time.sleep(0.5)
LED(3).on()
time.sleep(0.5)
LED(4).on()
time.sleep(1.5)
LED(1).off()
LED(2).off()
LED(3).off()
LED(4).off()

# Définit quels servos bouger pour faire chaque note
position_servos = {'C': (1, 1, 1, 1, 1, 1, 1), 'D': (1, 1, 1, 1, 1, 1, 0), 'E': (1, 1, 1, 1, 1, 0, 0),
                   'F': (1, 1, 1, 1, 0, 1, 1), 'G': (1, 1, 1, 0, 0, 0, 0),
                   'A': (1, 1, 0, 0, 0, 0, 0), 'B': (1, 0, 0, 0, 0, 0, 0)}

# Carte des Timers et channels associés à chaque Pin (physique)
# Syntaxe ; Pin : (Timer, Channel)
pyboard_map = {'X1': (5, 3), 'X2': (5, 4), 'X3': (5, 1), 'X4': (5, 2), 'X6': (2, 1), 'X7': (3, 1), 'X8': (3, 2),
               'X10': (4, 2), 'Y1': (3, 1), 'Y2': (3, 2), 'Y3': (2, 3), 'Y4': (4, 4),
               'Y9': (1, 1), 'Y10': (4, 3), 'Y11': (3, 3), 'Y12': (3, 4)}


# Calibration usuelle : 700,2550,1600,2600,2000

class PCA9685:
    def __init__(self, i2c, address=0x40):
        self.i2c = i2c
        self.address = address
        self.reset()
        self.setting = {}

    def _write(self, address, value):
        self.i2c.writeto_mem(self.address, address, bytearray([value]))

    def _read(self, address):
        return self.i2c.readfrom_mem(self.address, address, 1)[0]

    def setup(self, index):
        self.setup[index] = (0,0)      # pwm pour l'état 0 et 1
        self.calibrate(index)


    def reset(self):
        self._write(0x00, 0x00) # Mode1

    def freq(self, freq=None):
        if freq is None:
            return int(25000000.0 / 4096 / (self._read(0xfe) - 0.5))
        prescale = int(25000000.0 / 4096.0 / freq + 0.5)
        old_mode = self._read(0x00) # Mode 1
        self._write(0x00, (old_mode & 0x7F) | 0x10) # Mode 1, sleep
        self._write(0xfe, prescale) # Prescale
        self._write(0x00, old_mode) # Mode 1
        time.sleep_us(5)
        self._write(0x00, old_mode | 0xa1) # Mode 1, autoincrement on

    def pwm(self, index, on=None, off=None):
        if on is None or off is None:
            data = self.i2c.readfrom_mem(self.address, 0x06 + 4 * index, 4)
            return ustruct.unpack('<HH', data)
        data = ustruct.pack('<HH', on, off)
        self.i2c.writeto_mem(self.address, 0x06 + 4 * index,  data)

    def play(self,index, state):
        pass

    def calibrate(self, index):
        setup_complete = False
        pwm0 = 50
        pwm1 = 300
        previous_cmd = None
        print("calibration du servo-moteur : pwm entre 100 et 450, set0, set1, done.")
        while not setup_complete:
            move = input()
            if move == 'done':
                setup_complete = True
                self.setting[index] = (pwm0, pwm1)
            elif move == 'set0':
                pwm0 = int(previous_cmd)
            elif move == 'set1':
                pwm1 = int(previous_cmd)
            else:
                self.duty(index, int(move))
            previous_cmd = move

    def duty(self, index, value=None, invert=False):
        if value is None:
            pwm = self.pwm(index)
            if pwm == (0, 4096):
                value = 0
            elif pwm == (4096, 0):
                value = 4095
            value = pwm[1]
            if invert:
                value = 4095 - value
            return value
        if not 0 <= value <= 4095:
            raise ValueError("Out of range")
        if invert:
            value = 4095 - value
        if value == 0:
            self.pwm(index, 0, 4096)
        elif value == 4095:
            self.pwm(index, 4096, 0)
        else:
            self.pwm(index, 0, value)

