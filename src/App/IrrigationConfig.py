

class IrrigationConfig:

    IRRIGATION_CONFIG_TIME = "time"
    IRRIGATION_CONFIG_AMOUNT = "amount"
    IRRIGATION_CONFIG_ENABLED = "enabled"
    IRRIGATION_CONFIG_INTERVAL = "interval"
    IRRIGATION_CONFIG_PARTS = "parts"

    def __init__(self):
        self.Values = {IrrigationConfig.IRRIGATION_CONFIG_TIME: (12, 00, 00),
                       IrrigationConfig.IRRIGATION_CONFIG_AMOUNT: 10,
                       IrrigationConfig.IRRIGATION_CONFIG_ENABLED: False,
                       IrrigationConfig.IRRIGATION_CONFIG_PARTS: 1,
                       IrrigationConfig.IRRIGATION_CONFIG_INTERVAL: 1}

        self.Callbacks = {IrrigationConfig.IRRIGATION_CONFIG_TIME: None,
                          IrrigationConfig.IRRIGATION_CONFIG_AMOUNT: None,
                          IrrigationConfig.IRRIGATION_CONFIG_ENABLED: None,
                          IrrigationConfig.IRRIGATION_CONFIG_PARTS: None,
                          IrrigationConfig.IRRIGATION_CONFIG_INTERVAL: None}
        return

    def SetCallback(self, key, callback):
        if key in self.Callbacks.keys():
            self.Callbacks[key] = callback

    def SetValue(self, key, value):
        if key in self.Values.keys():
            self.Values[key] = value
