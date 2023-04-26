import can
import cantools
import time
import os

import cv2


if os.name == 'nt':
    bus = can.interface.Bus(channel=0, bustype='vector', bitrate=250000, fd=True)
else:
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan', bitrate=250000, fd=True)

dbc = """VERSION ""
BO_ 2566834709 TIM21: 8 SEND
 SG_ HitchPosReq : 10|2@1+ (1,0) [0|3] "%" Vector__XXX
 SG_ VehicleSpeedRequest : 12|2@1+ (1,0) [0|3] "m/s" Vector__XXX
BO_ 2362179474 PD_Sprayer: 14 Vector__XXX
  SG_ AppRateVolumePerArea_Act m2 : 32|32@1- (0.01,0) [0|21474836.47] "mm³/m²" Vector__XXX
"""

dm1 = cantools.db.load_string(dbc, 'dbc').get_message_by_name("TIM21")
pds = cantools.db.load_string(dbc, 'dbc').get_message_by_name("PD_Sprayer")

def send2can(message):
    bus.send(message)
    print(message)

value_thing = 0

def on_change(value):
    global value_thing
    value_thing = value

window_name = "Slider GUI"
cv2.namedWindow(window_name)
cv2.createTrackbar("ARVPA", window_name, 10, 300, on_change)


sleeptime = 2
while True:
    cv2.imshow(window_name, 0)
    
    key = cv2.waitKey(1)
    if key == ord("q"):
        break

    send2can(can.Message(arbitration_id=pds.frame_id, data=pds.encode({'AppRateVolumePerArea_Act': value_thing}), dlc=14, is_fd=True))
    send2can(can.Message(arbitration_id=dm1.frame_id, data=dm1.encode({'HitchPosReq': 1, 'VehicleSpeedRequest': 1})))
    time.sleep(sleeptime)

cv2.destroyAllWindows()