# upyiot modules
from upyiot.system.SystemTime.SystemTime import SystemTime
from upyiot.system.Service.ServiceScheduler import ServiceScheduler
from upyiot.system.Service.ServiceScheduler import Service
from upyiot.system.Util import ResetReason
from upyiot.comm.NetCon.NetCon import NetCon
from upyiot.middleware.SubjectObserver.SubjectObserver import Observer
from upyiot.middleware.Sensor import Sensor
from upyiot.drivers.Led.RgbLed import RgbLed
from upyiot.drivers.Board.Supply import Supply
from upyiot.drivers.Switches.TactSwitch import TactSwitch
from upyiot.drivers.Actuators.WaterPump import WaterPump
from upyiot.drivers.Sensors.FloatSensor import FloatSensor

# SmartPump modules
from Config.Hardware import Pins
from App.ConfigWebserver import ConfigWebserver
from App.IrrigationController import IrrigationController
from App.IrrigationConfig import IrrigationConfig

# micropython modules
import network
from network import WLAN
from micropython import const


class HwDrivers:

    def __init__(self):
        self.RgbLed = RgbLed(Pins.CFG_HW_PIN_LED_RED,
                             Pins.CFG_HW_PIN_LED_GREEN, Pins.CFG_HW_PIN_LED_BLUE)
        self.PumpMosfet = Supply(Pins.CFG_HW_PIN_PUMP_MOSFET, 1000)
        self.Pump = WaterPump(self.PumpMosfet, 800)
        self.Float = FloatSensor(Pins.CFG_HW_PIN_FLOAT_SENSOR)


class WlanHandover(Service):
    WLAN_HANDOVER_SERVICE_MODE = Service.MODE_RUN_ONCE

    def __init__(self, netcon_svc, wlan, sched, irrigation):
        super().__init__("WlanHovr", self.WLAN_HANDOVER_SERVICE_MODE, {})
        self.Wlan = wlan
        self.NetCon = netcon_svc
        self.Mode = NetCon.MODE_STATION
        self.Scheduler = sched
        self.Irrigation = irrigation


    def SvcInit(self):
        return

    def SvcRun(self):
        if self.Mode is NetCon.MODE_STATION:
            self.Scheduler.ServiceDeregister(self.NetCon)
            self.Wlan = WLAN(network.AP_IF)
            self.Scheduler.ServiceRegister(self.NetCon)
            self.NetCon.WlanInterface(self.Wlan, NetCon.MODE_ACCESS_POINT)
            self.Mode = NetCon.MODE_ACCESS_POINT
            self.NetCon.SvcActivate()
            #self.Scheduler.ServiceDeregister(self)
            self.Irrigation.SvcActivate()


class App(Observer):

    DIR = "./"
    FILTER_DEPTH = const(5)
    DEEPSLEEP_THRESHOLD_SEC = const(3600)

    FLOAT_SENSOR_READ_INTERVAL_SEC = const(1)

    def __init__(self, netcon):
        self.NetCon = netcon
        return

    def Setup(self):
        super().__init__()
        rst_reason = ResetReason.ResetReason()

        self.Drivers = HwDrivers()

        self.Config = IrrigationConfig()

        self.Webserver = ConfigWebserver(self.Config)

        self.Irrigation = IrrigationController(self.Drivers.Pump, self.Config, True)

        self.FloatSensor = Sensor.Sensor(self.DIR,
                                         "float",
                                         self.FILTER_DEPTH, self.Drivers.Float,
                                         self.FILTER_DEPTH, store_data=False)

        self.Time = SystemTime.InstanceGet()

        self.Scheduler = ServiceScheduler(self.DEEPSLEEP_THRESHOLD_SEC)

        # Set service dependencies.
        self.Time.SvcDependencies({self.NetCon: Service.DEP_TYPE_RUN_ALWAYS_BEFORE_RUN})

        # Register all services to the scheduler.
        self.Scheduler.ServiceRegister(self.Webserver)
        self.Scheduler.ServiceRegister(self.Irrigation)
        self.Scheduler.ServiceRegister(self.Time)
        self.Scheduler.ServiceRegister(self.NetCon)

        if rst_reason is not ResetReason.RESET_REASON_RTC:
            # Create the WLAN station interface.
            self.Wlan = WLAN(network.STA_IF)
            self.NetCon.WlanInterface(self.Wlan, NetCon.MODE_STATION)
            self.Handover = WlanHandover(self.NetCon, self.Wlan, self.Scheduler, self.Irrigation)
            self.Irrigation.SvcDependencies({self.Handover: Service.DEP_TYPE_RUN_ONCE_BEFORE_RUN,
                                             self.Time: Service.DEP_TYPE_RUN_ONCE_BEFORE_RUN})
            self.Webserver.SvcDependencies({self.Handover: Service.DEP_TYPE_RUN_ONCE_BEFORE_RUN,
                                            self.Time: Service.DEP_TYPE_RUN_ONCE_BEFORE_RUN})
            self.Handover.SvcDependencies({self.Time: Service.DEP_TYPE_RUN_ALWAYS_BEFORE_RUN})
            self.Scheduler.ServiceRegister(self.Handover)
            self.Handover.SvcActivate()

        else:
            self.Wlan = WLAN(network.AP_IF)
            self.NetCon.WlanInterface(self.Wlan, NetCon.MODE_ACCESS_POINT)
            self.Irrigation.SvcDependencies({self.Time: Service.DEP_TYPE_RUN_ONCE_BEFORE_RUN})
            self.Irrigation.SvcActivate()


        # Link the observers to the sensors.
        self.FloatSensor.ObserverAttachNewSample(self.Irrigation)

        self.FloatSensor.SvcIntervalSet(App.FLOAT_SENSOR_READ_INTERVAL_SEC)
        self.Irrigation.AttachStateObserver(self)


    def Run(self):
        self.Scheduler.Run()

    def Update(self, arg):
        if arg is IrrigationController.STATE_PUMPING:
            # Only register the FloatSensor service if it is not
            # in the list of services.
            if self.FloatSensor not in self.Scheduler.Services:
                self.Scheduler.ServiceRegister(self.FloatSensor)
                #self.Scheduler.ServiceDeregister(self.Webserver)
                self.Webserver.SvcMode = Service.MODE_RUN_ONCE
                self.Webserver.SvcDeactivate()
                self.FloatSensor.SvcActivate()
        elif arg is IrrigationController.STATE_WAITING:
            self.FloatSensor.SvcDeactivate()
            self.Scheduler.ServiceDeregister(self.FloatSensor)
            # self.Scheduler.ServiceRegister(self.Webserver)
            self.Webserver.SvcMode = Service.MODE_RUN_PERIODIC
            self.Webserver.SvcActivate()
