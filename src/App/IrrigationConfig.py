

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

        self.Callbacks = {}
        return

    def SetCallback(self, key, callback, context):
        if key not in self.Callbacks.keys():
            self.Callbacks[key] = (callback, context)

    def SetValue(self, key, value):
        if key in self.Values.keys():
            self.Values[key] = value
            if key in self.Callbacks.keys():
                print(self.Callbacks[key][0])
                print(self.Callbacks[key][1])
                self.Callbacks[key][0](self.Callbacks[key][1], value)
