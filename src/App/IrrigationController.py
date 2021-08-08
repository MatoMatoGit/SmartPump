from upyiot.system.Service.ServiceScheduler import Service
from upyiot.system.SystemTime.SystemTime import SystemTime
from upyiot.middleware.SubjectObserver.SubjectObserver import Observer
from upyiot.middleware.SubjectObserver.SubjectObserver import Subject
from micropython import const

from App.IrrigationConfig import IrrigationConfig


class IrrigationControllerService(Service):
    IRRIGATION_CONTROLLER_SERVICE_MODE = Service.MODE_RUN_PERIODIC

    def __init__(self):
        super().__init__("Irc", self.IRRIGATION_CONTROLLER_SERVICE_MODE, {})


class IrrigationController(IrrigationControllerService, Observer):

    POLL_INTERVAL = const(10)

    STATE_WAITING = const(0)
    STATE_PUMPING = const(1)
    STATE_EM_STOP = const(2)

    FLOAT_SENSOR_EM_STOP_VALUE = const(1)

    def __init__(self, pump_driver_obj, config):
        super().__init__()
        self.Pump = pump_driver_obj
        self.State = Subject()
        self.State.State = IrrigationController.STATE_WAITING
        self.Config = config
        self.PumpDurationSec = 0
        self.Time = SystemTime.InstanceGet()
        self.IntervalCount = 1
        return

    def SvcRun(self):
        if self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_ENABLED] is False:
            print("[IRC] Irrigation disabled.")
            self.SvcIntervalSet(self.POLL_INTERVAL)
            return

        print("[IRC] State: {}".format(self.State.State))

        # The controller is waiting for the right time to enable the pump.
        if self.State.State is IrrigationController.STATE_WAITING:
            print("[IRC] Waiting. Checking time schedule..")

            # Get the current time and compare it to the irrigation time.
            datetime = self.Time.Now()
            print("[IRC] Current time (HH:MM): {}:{}".format(datetime[self.Time.RTC_DATETIME_HOUR],
                                                          datetime[self.Time.RTC_DATETIME_MINUTE]))

            print("[IRC] Schedule time (HH:MM): {}:{}".format(self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_TIME][0],
                                                              self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_TIME][1]))

            # If the current time is later or at the set irrigation time,
            # enable the pump.
            if datetime[self.Time.RTC_DATETIME_HOUR] is self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_TIME][0]  \
                    and datetime[self.Time.RTC_DATETIME_MINUTE] is self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_TIME][1]:

                if self.IntervalCount is 1:
                    print("[IRC] Enabling pump.")
                    self.Pump.Enable()
                    self.State.State = IrrigationController.STATE_PUMPING

                    # Calculate the pump duration from the amount.
                    self.PumpDurationSec = self.Pump.DurationSecGet(self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_AMOUNT])
                    print("[IRC] Pumping for {} seconds".format(self.PumpDurationSec))
                    self.SvcIntervalSet(self.PumpDurationSec)
                    self.IntervalCount = self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_INTERVAL]
                    print("[IRC] Next irrigation in {} days".format(self.IntervalCount))
                    return
                else:
                    self.IntervalCount -= 1
                    print("[IRC] Skipping 1 day. Days left: {}".format(self.IntervalCount - 1))

        # The pump is enabled.
        elif self.State.State is IrrigationController.STATE_PUMPING:
            print("[IRC] Disabling pump")
            self.Pump.Disable()
            self.State.State = IrrigationController.STATE_WAITING
            self.SvcIntervalSet(60)
            return

        # An emergency stop has occurred because the float sensor was triggered.
        elif self.State.State is IrrigationController.STATE_EM_STOP:
            print("[IRC] Pump emergency stop.")
            self.State.State = IrrigationController.STATE_WAITING
            self.SvcIntervalSet(60)
            return

        self.SvcIntervalSet(self.POLL_INTERVAL)

    def AttachStateObserver(self, observer):
        self.State.Attach(observer)

    def Update(self, arg):
        if arg is IrrigationController.FLOAT_SENSOR_EM_STOP_VALUE:
            self._EmergencyStop()

    def _EmergencyStop(self):
        print("[IRC] Emergency! Stopping pump.")
        self.Pump.Disable()
        self.State.State = IrrigationController.STATE_EM_STOP
