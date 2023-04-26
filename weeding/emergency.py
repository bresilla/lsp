import can
import cantools
import os
import argparse
import roslibpy
import time

if os.name == 'nt':
    bus = can.interface.Bus(channel=0, bustype='vector', app_name="CANoe")
else:
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')


dbc = """VERSION ""
BO_ 2566834709 DM1: 8 SEND
  SG_ FlashRedStopLamp : 12|2@1+ (1,0) [0|3] "" Vector__XXX
  SG_ FlashAmberWarningLamp : 10|2@1+ (1,0) [0|3] "" Vector__XXX
"""

dm1 = cantools.db.load_string(dbc, 'dbc').get_message_by_name("DM1")

def send2can(message):
    print(can.bus.BusState)
    try:
        bus.send(message)
        print(message)
    except can.CanError:
        print("COULD NOT SEND THE MESSAGE")


class Errorer():
    def __init__(self):
        self.sleeper = 1
        self.bridge = roslibpy.Ros(host="150.140.148.140", port=2233)
        self.trigger = roslibpy.Topic(self.bridge, "/lspn/error", 'std_msgs/Bool')

    def send_topic(self, topic, message):
        topic.publish(roslibpy.Message(message))
        print(message)

    def sleep(self):
        time.sleep(self.sleeper)


def main(args=None):
    erry = Errorer()

    while not erry.bridge.is_connected:
        try:
            print("BRIDGE CONNECTED")
            erry.bridge.run()
        except:
            print("BRIDGE NOT CONNECTED")
            time.sleep(5)

    while True:
        erry.send_topic(erry.trigger, {'data': True})
        send2can(
            can.Message(
                arbitration_id=dm1.frame_id,
                data=dm1.encode({'FlashAmberWarningLamp': 1 , 'FlashRedStopLamp': 1})
            )
        )
        erry.sleep()


if __name__ == '__main__':
    main()