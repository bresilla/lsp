import can
import cantools
import os
import time

if os.name == 'nt':
    bus = can.interface.Bus(channel=0, bustype='vector', app_name="CANoe")
else:
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')


dbc = """VERSION ""
BO_ 2566834709 TIM21: 8 SEND
 SG_ HitchPosReq : 10|2@1+ (1,0) [0|3] "%" Vector__XXX
 SG_ VehicleSpeedRequest : 12|2@1+ (1,0) [0|3] "m/s" Vector__XXX
"""

dm1 = cantools.db.load_string(dbc, 'dbc').get_message_by_name("TIM21")

def send2can(message):
    print(can.bus.BusState)
    try:
        bus.send(message)
        print(message)
    except can.CanError:
        print("COULD NOT SEND THE MESSAGE")


sleeptime = 2
while True:
    send2can(can.Message(arbitration_id=dm1.frame_id, data=dm1.encode({'HitchPosReq': 0, 'VehicleSpeedRequest': 0})))
    time.sleep(sleeptime)

    send2can(can.Message(arbitration_id=dm1.frame_id, data=dm1.encode({'HitchPosReq': 1, 'VehicleSpeedRequest': 1})))
    time.sleep(sleeptime)