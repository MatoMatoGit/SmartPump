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
    QUARTER_MINUTE_INTERVAL = const(60)
    SETTLE_PERIOD = const(80)

    STATE_WAITING = const(0)
    STATE_PUMPING = const(1)
    STATE_EMC_STOP = const(2)
    STATE_SETTLING = const(3)

    FLOAT_SENSOR_EM_STOP_VALUE = const(1)

    def __init__(self, pump_driver_obj, config, emc_stop=False):
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
        self.EmcStopEnabled = emc_stop
        return

    def SvcRun(self):
        if self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_ENABLED] is False:
            print("[IRC] Irrigation disabled.")
            self.SvcIntervalSet(self.POLL_INTERVAL)
            return

        print("[IRC] State: {}".format(self.State.State))


        # An emergency stop has occurred because the float sensor was triggered.
        if self.State.State is IrrigationController.STATE_EMC_STOP:
            print("[IRC] Pump emergency stop.")
            self.State.State = IrrigationController.STATE_WAITING
            # Wait longer than 1 minute to make sure the window to reactivate the pump passes.
            self.SvcIntervalSet(self.QUARTER_MINUTE_INTERVAL * 5)

        # The controller is waiting for the right time to enable the pump.
        elif self.State.State is IrrigationController.STATE_WAITING:
            print("[IRC] Waiting. Checking time schedule..")

            # Get the current time and compare it to the irrigation time.
            datetime = self.Time.Now()
            hour_now = datetime[self.Time.RTC_DATETIME_HOUR] + 2 # Convert UTC to NL time.
            minute_now = datetime[self.Time.RTC_DATETIME_MINUTE]
            hour_schedule = self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_TIME][0]
            minute_schedule = self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_TIME][1]

            print("[IRC] Current time (HH:MM): {}:{}".format(hour_now, minute_now))

            print("[IRC] Schedule time (HH:MM): {}:{}".format(hour_schedule, minute_schedule))

            # If the current time is later or at the set irrigation time,
            # enable the pump.
            if hour_now is hour_schedule and minute_now is minute_schedule:

                # Check if a day needs to be skipped.
                if self.IntervalCount is 1:
                    amount = self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_AMOUNT]
                    self.PartsTotal = self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_PARTS]

                    # Calculate the pump duration from the amount.
                    self.PumpDurationPerPart = int(self.Pump.DurationSecGet(
                        amount / self.PartsTotal))
                    self.PartsLeft = self.PartsTotal
                    print("[IRC] {} mL in {} parts".format(amount, self.PartsLeft))
                    
                    self.IntervalCount = self.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_INTERVAL]

                    self._StartPumpAndTransition(self.STATE_PUMPING)
                    self.SvcIntervalSet(self.PumpDurationPerPart)
                else:
                    self.IntervalCount -= 1
                    print("[IRC] Skipping 1 day. Days left: {}".format(self.IntervalCount))
            
            else:
                self.SvcIntervalSet(self.QUARTER_MINUTE_INTERVAL) # Restore default interval in case anything else was set.

        # The pump is enabled when entering this state.
        elif self.State.State is IrrigationController.STATE_PUMPING:
            if self.PartsLeft > 1:
                self._StopPumpAndTransition(self.STATE_SETTLING)
                self.SvcIntervalSet(self.SETTLE_PERIOD)
            else:
                print("[IRC] Next irrigation in {} days".format(self.IntervalCount))
                self._StopPumpAndTransition(self.STATE_WAITING)
                self.SvcIntervalSet(self.QUARTER_MINUTE_INTERVAL)

        # The pump is temporarily disabled when entering this state.
        # This has been done to let the water settle.
        elif self.State.State is self.STATE_SETTLING:
            if self.PartsLeft > 1:
                self.PartsLeft -= 1
                self._StartPumpAndTransition(self.STATE_PUMPING)
                self.SvcIntervalSet(self.PumpDurationPerPart)
            else:
                print("[IRC] Next irrigation in {} days".format(self.IntervalCount))
                self._StopPumpAndTransition(self.STATE_WAITING)
                self.SvcIntervalSet(self.QUARTER_MINUTE_INTERVAL)

        # No valid pump state.
        else:
            raise Exception()

    def AttachStateObserver(self, observer):
        self.State.Attach(observer)

    def Update(self, arg):
        if arg is IrrigationController.FLOAT_SENSOR_EM_STOP_VALUE:
            self._EmergencyStop()

    def _EmergencyStop(self):
        if self.EmcStopEnabled is True:
            print("[IRC] Emergency! Stopping pump.")
            self._StopPumpAndTransition(self.STATE_EMC_STOP)
            self.SvcIntervalSet(self.POLL_INTERVAL) # Set shorter service interval to handle emergency stop.

    def _CurrentPart(self):
        return self.PartsTotal - self.PartsLeft

    def _StartPumpAndTransition(self, next_state: int):
        print("[IRC] Pumping part {}: {} seconds".format(self._CurrentPart(), self.PumpDurationPerPart))
        self.Pump.Enable()
        print("[IRC] Next state: {}".format(next_state))
        self.State.State = next_state
    
    def _StopPumpAndTransition(self, next_state: int):
        print("[IRC] Disabling pump")
        self.Pump.Disable()
        print("[IRC] Next state: {}".format(next_state))
        self.State.State = next_state