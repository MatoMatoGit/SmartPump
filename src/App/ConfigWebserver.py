from upyiot.system.Service.ServiceScheduler import Service
from upyiot.comm.Web.Webserver import Webserver

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

    Webpage = """<html><head>
            <title>""" + WebpageTitle + """</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="icon" href="data:,">
            <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
            h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none;
            border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
            .button2{background-color: #4286f4;}
            </style>
            </head>
            <body> <h1>""" + WebpageTitle + """</h1>
            <h2>Pump ID: """ + ID + """</h2>
            <form action="/irrigation_settings">
            Tijd: <input type="time" name="time" value="12:00:00"><br>
            Hoeveelheid (mL): <input type="number" name="amount" value="10"><br>
            <input type="submit" value="Toepassen">
            </form>
            </body>
            </html>"""

    Time = None
    Amount = None

    def __init__(self):
        super().__init__(ConfigWebserver.Webpage)

        self.RegisterQueryHandle('time', ConfigWebserver.QueryHandleTime, self)
        self.RegisterQueryHandle('amount', ConfigWebserver.QueryHandleAmount, self)

    def QueryHandleTime(query, value):
        print("{}:{}".format(query, value))
        ConfigWebserver.Time = value

    def QueryHandleAmount(query, value):
        print("{}:{}".format(query, value))
        ConfigWebserver.Amount = value

    def ConfigGet(self):
        if self.Time is None or self.Amount is None:
            return None

        return self.Time, self.Amount
