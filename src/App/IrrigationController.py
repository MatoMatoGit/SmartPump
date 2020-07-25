from upyiot.system.Service.ServiceScheduler import Service
from upyiot.system.SystemTime.SysterTime import SystemTime
from upyiot.middleware.SubjectObserver.SubjectObserver import Observer
from micropython import const


class IrrigationControllerService(Service):
    IRRIGATION_CONTROLLER_SERVICE_MODE = Service.MODE_RUN_PERIODIC

    def __init__(self):
        super().__init__("Irc", self.IRRIGATION_CONTROLLER_SERVICE_MODE, {})


class IrrigationController(IrrigationControllerService, Observer):

    STATE_WAITING = const(0)
    STATE_PUMPING = const(1)
    STATE_EM_STOP = const(2)

    FLOAT_SENSOR_EM_STOP_VALUE = const(1)

    def __init__(self, pump_driver_obj):
        super().__init__()
        self.Pump = pump_driver_obj
        self.State = IrrigationController.STATE_WAITING
        self.Config = None
        self.PumpDurationSec = 0
        self.Time = SystemTime.InstanceGet()
        return

    def SvcRun(self):
        if self.Config is None:
            self.SvcIntervalSet(5)

        # The controller is waiting for the right time to enable the pump.
        if IrrigationController.STATE_WAITING:
            # Get the current time and compare it to the irrigation time.
            datetime = self.Time.Now()

            # If the current time is later or at the set irrigation time,
            # enable the pump.
            if datetime(self.Time.RTC_DATETIME_HOUR) >= self.Config(1)(0)  \
                    and datetime(self.Time.RTC_DATETIME_MINUTE) >= self.Config(1)(1):
                self.Pump.Enable()
                self.State = IrrigationController.STATE_PUMPING

                # Calculate the pump duration from the amount.
                self.PumpDurationSec = self.Pump.DurationSecGet(self.Config(0))
                self.SvcIntervalSet(self.PumpDurationSec)

        # The pump is enabled.
        if IrrigationController.STATE_PUMPING:
            self.Pump.Disable()
            self.State = IrrigationController.STATE_WAITING
            self.SvcIntervalSet(3)

        # An emergency stop has occurred because the float sensor was triggered.
        if IrrigationController.STATE_EM_STOP:
            self.State = IrrigationController.STATE_WAITING

    def Update(self, arg):
        if arg is IrrigationController.FLOAT_SENSOR_EM_STOP_VALUE:
            self._EmergencyStop()

    def ConfigSet(self, config):
        self.Config = config

    def _EmergencyStop(self):
        self.Pump.Disable()
        self.State = IrrigationController.STATE_EM_STOP
