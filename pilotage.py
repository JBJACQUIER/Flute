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


class Servo:
    """Objets Servo pour commande des servomoteurs en PWM (Pulse Width Modulation)"""

    # Configuration des pins
    def __init__(self, nom: str):
        self.pin = Pin(nom)  # Board name

        # Test Pin utilisable pour commande en PWM
        if nom not in pyboard_map:
            raise Exception("Pin('{}') is not available for PWM use (no Timer associated) \n  "
                            "try using another pin".format(nom))

        self.timer = None  # On travaille en PWM à 50 Hz
        self.channel = None
        self.state = 0  # Actif ou passif
        self.calibration = {0: 5, 1: 7.5}  # Donne le pulse width percent associe a chaque état
        self.pwm = None
        self._setup()

    def _get_timer(self):
        """ Permet d'utiliser un timer accessible au pin à l'aide de pyboard_map """
        board_pin = self.pin.names()[1]
        self.timer, self.channel = Timer(pyboard_map[board_pin][0], freq=50), pyboard_map[board_pin][1]

    def _setup(self):
        """Initialise le Pin pour la commande en PWM"""
        self._get_timer()  # On crée un timer accessible au pin, de fréquence 50Hz
        self.pwm = self.timer.channel(self.channel, Timer.PWM, pin=self.pin, pulse_width_percent=self.calibration[0])

    def play(self, etat):
        """Permet de jouer les notes, en oscillant entre les états 0 et 1 (actif et passif)"""
        assert self.pwm is not None
        self.pwm = self.timer.channel(self.channel, Timer.PWM, pin=self.pin, pulse_width_percent=self.calibration[etat])
        self.state = etat

    def free_move(self, pwp):
        self.pwm = self.timer.channel(self.channel, Timer.PWM, pin=self.pin, pulse_width_percent=pwp)
        self.state = None

    def set01(self):
        setup_complete = False
        pwm0 = 5
        pwm1 = 7.5
        previous_cmd = 0
        print("calibration du servo-moteur")
        while not setup_complete:
            move = input()
            if move == 'done':
                setup_complete = True
                self.calibration[0] = pwm0
                self.calibration[1] = pwm1
            elif move == 'set0':
                pwm0 = float(previous_cmd)
            elif move == 'set1':
                pwm1 = float(previous_cmd)
            else:
                self.free_move(float(move))
            previous_cmd = move


class Flute:
    """Objet flûte, permet la coordination des servos associés à une flûte pour jouer une note spécifique"""

    def __init__(self, numero_flute: int = 0, board_pins: tuple = ('Y1', 'Y2', 'Y3', 'Y4', 'Y9', 'Y10', 'Y11')):
        LED(3).on()
        self.num_flute = numero_flute  # 0 to 2
        try:
            self.servomoteurs = [Servo(pins) for pins in board_pins]
        except KeyError:
            raise Exception('A Pin is not available')
        time.sleep(0.2)
        LED(4).on()

        time.sleep(2)
        LED(3).off()
        LED(4).off()

    def __repr__(self):
        return 'flute {}, {}'.format(self.num_flute, self.servomoteurs)

    def __str__(self):
        return 'Flûte n°{} \n servos : {}'.format(self.num_flute, self.servomoteurs)

    def jouer_note(self, note: str):
        """Actualise tous les servomoteurs d'une flûte, afin de jouer une note."""
        LED(4).on()
        for i in range(len(position_servos[note])):
            self.servomoteurs[i].play(position_servos[note][i])
        time.sleep(1)
        LED(4).off()


class Detection:
    """À utiliser pour les capteurs ultrasons."""
    pass


class PCA9685:
    def __init__(self, i2c, address=0x40):
        self.i2c = i2c
        self.address = address
        self.reset()
        self.setup = {}

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
        previous_cmd = 0
        print("calibration du servo-moteur")
        while not setup_complete:
            move = input()
            if move == 'done':
                setup_complete = True
                self.calibration[0] = pwm0
                self.calibration[1] = pwm1
            elif move == 'set0':
                pwm0 = float(previous_cmd)
            elif move == 'set1':
                pwm1 = float(previous_cmd)
            else:
                self.free_move(float(move))
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

