from upyiot.system.SystemTime.SystemTime import SystemTime
from upyiot.system.Service.ServiceScheduler import ServiceScheduler
from upyiot.system.Service.ServiceScheduler import Service
from upyiot.system.Util import ResetReason
from upyiot.comm.NetCon.NetCon import NetCon
from upyiot.middleware.Sensor import Sensor

from upyiot.drivers.Led.Led import RgbLed
from upyiot.drivers.Board.Supply import Supply
from upyiot.drivers.Switches.TactSwitch import TactSwitch
from upyiot.drivers.Actuators.WaterPump import WaterPump
from upyiot.drivers.Sensors.FloatSensor import FloatSensor

from App.ConfigWebserver import ConfigWebserver
from App.IrrigationController import IrrigationController

from micropython import const


class HwDrivers:

    def __init__(self):
        self.RgbLed = RgbLed(11, 12, 13)
        self.PumpRelay = Supply(1, 200)
        self.Pump = WaterPump(self.PumpRelay, 200)
        self.Float = FloatSensor(3)


class App:

    DIR = "./"
    FILTER_DEPTH = const(20)
    DEEPSLEEP_THRESHOLD_SEC = const(5)

    NetCon = None

    def __init__(self):
        return

    def Setup(self):

        self.Drivers = HwDrivers()

        self.Webserver = ConfigWebserver()

        self.Irrigation = IrrigationController(self.Drivers.Pump)

        self.FloatSensor = Sensor.Sensor(self.DIR,
                                         "float",
                                         self.FILTER_DEPTH, self.Drivers.Float,
                                         self.FILTER_DEPTH)

        self.Time = SystemTime.InstanceGet()
        self.NetCon.WlanInterface(wlan_ap, NetCon.MODE_STATION)

        self.Scheduler = ServiceScheduler(self.DEEPSLEEP_THRESHOLD_SEC)

        # Set service dependencies.
        self.Time.SvcDependencies({self.NetCon: Service.DEP_TYPE_RUN_ALWAYS_BEFORE_RUN})
        self.FloatSensor.SvcDependencies({self.Time: Service.DEP_TYPE_RUN_ONCE_BEFORE_RUN})
        self.Webserver.SvcDependencies({self.Time: Service.DEP_TYPE_RUN_ONCE_BEFORE_RUN})
        self.Irrigation.SvcDependencies({self.Time: Service.DEP_TYPE_RUN_ONCE_BEFORE_RUN})

        # Register all services to the scheduler.
        self.Scheduler.ServiceRegister(self.Time)
        self.Scheduler.ServiceRegister(self.NetCon)
        self.Scheduler.ServiceRegister(self.FloatSensor)
        self.Scheduler.ServiceRegister(self.Webserver)
        self.Scheduler.ServiceRegister(self.Irrigation)

        # Link the observers to the sensors.
        self.FloatSensor.ObserverAttachNewSample(self.Irrigation)




