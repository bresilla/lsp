import can
import cantools
import os

if os.name == 'nt':
    bus = can.interface.Bus(channel=0, bustype='vector', app_name="CANoe")
else:
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')


dbc = """VERSION ""
BO_ 2365194522 PD_Loader: 8 SEND
  SG_ Quality : 0|32@1+ (1,0) [0|100] "%"  Loader
  SG_ Capacity : 32|32@1+ (1,0) [0|4294967295] "mm2/s"  Loader
BO_ 2566834709 DM1: 8 SEND
  SG_ FlashRedStopLamp : 12|2@1+ (1,0) [0|3] "" Vector__XXX
  SG_ FlashAmberWarningLamp : 10|2@1+ (1,0) [0|3] "" Vector__XXX
"""


clock = 0.5
quality = 0
capacity = 0
emergency = False
cameras = True

dm1 = cantools.db.load_string(dbc, 'dbc').get_message_by_name("DM1")
pdl = cantools.db.load_string(dbc, 'dbc').get_message_by_name("PD_Loader")

def send2can(message):
    print(can.bus.BusState)
    try:
        bus.send(message)
        print(message)
    except can.CanError:
        print("COULD NOT SEND THE MESSAGE")


def callback(dt):
    send2can(can.Message(arbitration_id=pdl.frame_id, data=pdl.encode({'Capacity': capacity, 'Quality': quality})))
    send2can(can.Message(arbitration_id=dm1.frame_id, data=dm1.encode({'FlashAmberWarningLamp': int(cameras), 'FlashRedStopLamp': int(emergency)})))
    print("-----")


class MyLayout():


class MyApp(App):
    def build(self):
        return MyLayout()


if __name__ == "__main__":
    Clock.schedule_interval(callback, clock)
    MyApp().run()