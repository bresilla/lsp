import can
import cantools
import os
import time

if os.name == 'nt':
    bus = can.interface.Bus(channel=2, bustype='vector', app_name="CANoe", )
else:
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')


msg0 = can.Message(
    arbitration_id=0x1c24ff83,
    data=[0x00, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00],
    is_extended_id=True
)

msg1 = can.Message(
    arbitration_id=0x1c24ff83,
    data=[0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    is_extended_id=True
)


def send_can(message):
    print(can.bus.BusState)
    try:
        bus.send(message)
        print(message)
    except can.CanError:
        print("COULD NOT SEND THE MESSAGE")



sleeptime = 0.1
while True:
    send_can(msg0)
    # print(msg0.data[0])
    time.sleep(sleeptime)

    # send_can(msg1)
    # time.sleep(sleeptime)