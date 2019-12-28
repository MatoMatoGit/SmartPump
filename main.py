from machine import Pin
import utime

from upyiot.drivers.Led.Led import RgbLed
from upyiot.drivers.Switches.TactSwitch import TactSwitch

class LevelSensor:

    def __init__(self, en_pin_nr, sense_pin_nr, cb_state_change, context):
        self.EnPin = Pin(en_pin_nr, Pin.OUT)
        self.SensePin = Pin(sense_pin_nr, Pin.OUT)
        self.CbStateChange = cb_state_change
        self.Context = context

    def Enable(self):
        self.SensePin.irq(trigger=(Pin.IRQ_RISING | Pin.IRQ_FALLING),
                          handler=self.CbStateChange(self.Context))
        self.EnPin.on()

    def Disable(self):
        self.SensePin.irq(trigger=None,
                          handler=None)
        self.EnPin.off()

    def State(self):
        return self.EnPin.value()


class Relay:

    def __init__(self, en_pin_nr):
        self.EnPin = Pin(en_pin_nr, Pin.OUT)
        self.Enabled = False

    def Enable(self):
        if self.Enabled is True:
            return

        self.EnPin.on()
        utime.sleep_ms(250)
        self.Enabled = True

    def Disable(self):
        if self.Enabled is False:
            return

        self.EnPin.off()
        utime.sleep_ms(250)
        self.Enabled = False


def lvl_change(hw_drivers):
    hw_drivers.Relay.Disable()
    hw_drivers.RgbLed.Blue.Off()
    hw_drivers.RgbLed.Red.On()


class HwDrivers:

    def __init__(self):
        self.RgbLed = RgbLed(11, 12, 13)
        self.Relay = Relay(22)
        self.LvlSensor = LevelSensor(34, 26, lvl_change, self)


def main():
    # Create LED driver instances.
    drivers = HwDrivers()
    drivers.LvlSensor.Enable()

    while True:
        drivers.RgbLed.Blue.On()

        drivers.Relay.Enable()

        utime.sleep(5)

        drivers.Relay.Disable()

        drivers.RgbLed.Blue.Off()

        utime.sleep(2)


if __name__ == '__main__':
    main()
