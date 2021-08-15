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
    MINUTE_INTERVAL = const(60)
    SETTLE_PERIOD = const(80)

    STATE_WAITING = const(0)
    STATE_PUMPING = const(1)
    STATE_EM_STOP = const(2)
    STATE_SETTLING = const(3)

    FLOAT_SENSOR_EM_STOP_VALUE = const(1)

    def __init__(self, pump_driver_obj, config):
        super().__init__()
        self.Pump = pump_driver_obj
        self.State = Subject()
        self.State.State = IrrigationController.STATE_WAITING
        self.Config = config
        self.PumpDurationPerPart = 0
        self.Time = SystemTime.InstanceGet()
        self.IntervalCount = 1
        self.PartsLeft = 1
        self.PartsTotal = 1
        return

    def SvcRun(self):
        if self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_ENABLED] is False:
            print("[IRC] Irrigation disabled.")
            self.SvcIntervalSet(self.POLL_INTERVAL)
            return

        print("[IRC] State: {}".format(self.State.State))


        # An emergency stop has occurred because the float sensor was triggered.
        if self.State.State is IrrigationController.STATE_EM_STOP:
            print("[IRC] Pump emergency stop.")
            self.State.State = IrrigationController.STATE_WAITING
            self.SvcIntervalSet(self.MINUTE_INTERVAL)
            return

        # The controller is waiting for the right time to enable the pump.
        elif self.State.State is IrrigationController.STATE_WAITING:
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
                    amount = self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_AMOUNT]
                    self.PartsTotal = self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_PARTS]

                    # Calculate the pump duration from the amount.
                    self.PumpDurationPerPart = int(self.Pump.DurationSecGet(
                        amount / self.PartsTotal))
                    self.PartsLeft = self.PartsTotal

                    print("[IRC] {} mL in {} parts".format(amount, self.PartsLeft))

                    print("[IRC] Pumping part {}: {} seconds".format((self.PartsTotal - self.PartsLeft), self.PumpDurationPerPart))
                    self.SvcIntervalSet(self.PumpDurationPerPart)
                    self.IntervalCount = self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_INTERVAL]

                    print("[IRC] Enabling pump.")
                    self.Pump.Enable()
                    self.State.State = IrrigationController.STATE_PUMPING
                    return
                else:
                    self.IntervalCount -= 1
                    print("[IRC] Skipping 1 day. Days left: {}".format(self.IntervalCount - 1))

        # The pump is enabled.
        elif self.State.State is IrrigationController.STATE_PUMPING:
            if self.PartsLeft > 1:
                print("[IRC] Settling part {}: {} seconds".format((self.PartsTotal - self.PartsLeft), self.SETTLE_PERIOD))
                self.Pump.Disable()
                self.State.State = IrrigationController.STATE_SETTLING
                self.SvcIntervalSet(self.SETTLE_PERIOD)
                return
            else:
                print("[IRC] Disabling pump")
                self.Pump.Disable()
                print("[IRC] Next irrigation in {} days".format(self.IntervalCount))
                self.State.State = IrrigationController.STATE_WAITING
                self.SvcIntervalSet(self.MINUTE_INTERVAL)
                return

        # The pump is temporarily disabled to let the water settle.
        elif self.State.State is self.STATE_SETTLING:
            if self.PartsLeft > 1:
                self.PartsLeft -= 1
                print("[IRC] Pumping part {}: {} seconds".format((self.PartsTotal - self.PartsLeft), self.PumpDurationPerPart))
                self.Pump.Enable()
                self.State.State = IrrigationController.STATE_PUMPING
                self.SvcIntervalSet(self.PumpDurationPerPart)
                return
            else:
                print("[IRC] Disabling pump")
                self.Pump.Disable()
                print("[IRC] Next irrigation in {} days".format(self.IntervalCount))
                self.State.State = IrrigationController.STATE_WAITING
                self.SvcIntervalSet(self.MINUTE_INTERVAL)
                return

        # No valid pump state.
        else:
            raise Exception()

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
