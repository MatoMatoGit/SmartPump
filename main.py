from machine import Pin
import utime

from upyiot.drivers.Led.Led import RgbLed
from upyiot.drivers.Board.Supply import Supply
from upyiot.drivers.Switches.TactSwitch import TactSwitch
from upyiot.drivers.Actuators.WaterPump import WaterPump
from upyiot.drivers.Sensors.FloatSensor import FloatSensor


class HwDrivers:

    def __init__(self):
        self.RgbLed = RgbLed(11, 12, 13)
        self.PumpRelay = Supply(1, 200)
        self.Pump = WaterPump(self.PumpRelay, 200)
        self.FloatSensor = FloatSensor(3)


def main():

    drivers = HwDrivers()



    while True:
        drivers.RgbLed.Blue.On()

        drivers.Pump.Enable()

        utime.sleep(5)

        drivers.Pump.Disable()

        drivers.RgbLed.Blue.Off()

        utime.sleep(2)


if __name__ == '__main__':
    main()
