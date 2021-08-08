from upyiot.system.Service.ServiceScheduler import Service
from upyiot.comm.Web.Webserver import Webserver

from App.IrrigationConfig import IrrigationConfig

# Other
import network
from micropython import const
import machine
import ubinascii
import utime


class ConfigWebserver(Webserver):

    DIR = "./"
    ID = str(ubinascii.hexlify(machine.unique_id()).decode('utf-8'))
    ApCfg = {"ssid": "SmartPump-" + ID, "pwd": "mato", "ip": "192.168.0.200"}

    WebpageTitle = "SmartPump - Instellingen"
    Config = None

    def __init__(self, config):
        ConfigWebserver.Config = config

        self.Webpage = """"""
        self.UpdateWebpage()

        super().__init__(self.Webpage, 3)

        self.RegisterQueryHandle('time', ConfigWebserver.QueryHandleTime, self)
        self.RegisterQueryHandle('amount', ConfigWebserver.QueryHandleAmount, self)
        self.RegisterQueryHandle('enabled', ConfigWebserver.QueryHandleEnabled, self)
        self.RegisterQueryHandle('interval', ConfigWebserver.QueryHandleInterval, self)
        self.RegisterQueryHandle('parts', ConfigWebserver.QueryHandleParts, self)

    def QueryHandleTime(self, query, value):
        print("{}:{}".format(query, value))
        hr = int(value.split('%3A')[0])
        mins = int(value.split('%3A')[1])
        print("Set time {}:{}".format(hr, mins))
        ConfigWebserver.Config.SetValue(IrrigationConfig.IRRIGATION_CONFIG_TIME, (hr, mins))
        self.UpdateWebpage()

    def QueryHandleAmount(self, query, value):
        print("{}:{}".format(query, value))
        ConfigWebserver.Config.SetValue(IrrigationConfig.IRRIGATION_CONFIG_AMOUNT, int(value))
        self.UpdateWebpage()

    def QueryHandleEnabled(self, query, value):
        print("{}:{}".format(query, value))
        if value is "false":
            value = False
        else:
            value = True
        ConfigWebserver.Config.SetValue(IrrigationConfig.IRRIGATION_CONFIG_ENABLED, value)
        self.UpdateWebpage()

    def QueryHandleInterval(self, query, value):
        print("{}:{}".format(query, value))
        value = int(value)
        if value < 1:
            value = 1
        ConfigWebserver.Config.SetValue(IrrigationConfig.IRRIGATION_CONFIG_INTERVAL, value)
        self.UpdateWebpage()

    def QueryHandleParts(self, query, value):
        print("{}:{}".format(query, value))
        value = int(value)
        if value < 1:
            value = 1
        ConfigWebserver.Config.SetValue(IrrigationConfig.IRRIGATION_CONFIG_PARTS, value)
        self.UpdateWebpage()

    def UpdateWebpage(self):
        if ConfigWebserver.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_ENABLED] is True:
            radio_enabled = "checked"
            radio_disabled = ""
        else:
            radio_enabled = ""
            radio_disabled = "checked"

        self.Webpage = """<html><head>
                <title>""" + self.WebpageTitle + """</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link rel="icon" href="data:,">
                <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
                h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none;
                border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
                .button2{background-color: #4286f4;}
                </style>
                </head>
                <body> <h1>""" + self.WebpageTitle + """</h1>
                <h2>Pump ID: """ + self.ID + """</h2>
                <form action="/irrigation_settings">
                Tijd: <input type="time" name="time" value=\"""" + str(ConfigWebserver.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_TIME][0]) + \
                """:""" + str(ConfigWebserver.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_TIME][1]) + """\"><br>
                Hoeveelheid (mL): <input type="number" name="amount" value=\"""" + \
                str(ConfigWebserver.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_AMOUNT]) + """\"><br>
                Delen: <input type="number" name="parts" value=\"""" + \
                str(ConfigWebserver.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_PARTS]) + """\"><br>
                Interval (dagen): <input type="number" name="interval" value=\"""" + \
                str(ConfigWebserver.Config.Values[IrrigationConfig.IRRIGATION_CONFIG_INTERVAL]) + """\"><br>
                <p>Ingeschakeld</p>
                <input type="radio" id="true" name="enabled" value="true" """ + radio_enabled + """><br>
                <label for="true">Ja</label><br>
                <input type="radio" id="false" name="enabled" value="false" """ + radio_disabled + """><br>
                <label for="false">Nee</label><br>
                <input type="submit" value="Toepassen">
                </form>
                </body>
                </html>"""

        self.UpdatePage(self.Webpage)
