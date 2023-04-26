# import cantools
# import can

# db = cantools.database.load_file("my_can_database.dbc")
# signal = db.get_signal_by_name("Engine_Speed")
# encoded_value = signal.encode(3000)

# message_id = 0x123 # Replace with the ID of the message containing the signal
# message_data = bytearray(encoded_value)
# message = can.Message(arbitration_id=message_id, data=message_data)

# bus = can.Bus(interface='socketcan', channel='vcan0', bitrate=500000)
# bus.send(message)


# import can
# import cantools
# import os
# import time

# if os.name == 'nt':
#     bus = can.interface.Bus(channel=2, bustype='vector', app_name="CANoe", )
# else:
#     bus = can.interface.Bus(channel='vcan0', bustype='socketcan')


# dbc = """VERSION ""
# BO_ 472186755 TIM21: 8 TIM21
#  SG_ Process_Mulfunction : 16|16@1+ (1,0) [0|3] "" Vector__XXX
# """

# tim_id = 0x419351061
# tim = cantools.db.load_string(dbc, 'dbc').get_message_by_name("TIM21")

# def send_can(message):
#     print(can.bus.BusState)
#     try:
#         bus.send(message)
#         print(message)
#     except can.CanError:
#         print("COULD NOT SEND THE MESSAGE")

# def recv_can(db, id):
#     data = None
#     for i in range(20):
#         try:
#             message = bus.recv()
#             if message.arbitration_id == id:
#                 data = db.decode(message.data)
#                 print(data)
#         except can.CanError:
#             print("MESSAGE NOT RECIEVED")
#     return data

# # tim_message = recv_can(tim, tim_id)
# # print(tim_message)



# sleeptime = 2
# while True:
#     send_can(can.Message(is_extended_id=True, arbitration_id=tim.frame_id, data=tim.encode({'Process_Mulfunction': 0})))
#     time.sleep(sleeptime)

#     send_can(can.Message(is_extended_id=True, arbitration_id=tim.frame_id, data=tim.encode({'Process_Mulfunction': 1})))
#     time.sleep(sleeptime)



#---------------------------------------

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
    data=[0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00],
    is_extended_id=True
)

msg1 = can.Message(
    arbitration_id=0x1c24ff83,
    data=[0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    is_extended_id=True
)


# dbc = """VERSION ""
# BO_ 472186755 TIM21: 8 TIM21
#  SG_ Process_Mulfunction : 16|16@1+ (1,0) [0|3] "" Vector__XXX
# """

# tim_id = 0x419351061
# tim = cantools.db.load_string(dbc, 'dbc', strict=False)
# tim2 = tim.get_message_by_name("TIM21")

def send_can(message):
    print(can.bus.BusState)
    try:
        bus.send(message)
        print(message)
    except can.CanError:
        print("COULD NOT SEND THE MESSAGE")

# def recv_can(db, id):
#     data = None
#     for i in range(20):
#         try:
#             message = bus.recv()
#             if message.arbitration_id == id:
#                 data = db.decode(message.data)
#                 print(data)
#         except can.CanError:
#             print("MESSAGE NOT RECIEVED")
#     return data

# # tim_message = recv_can(tim, tim_id)
# # print(tim_message)



sleeptime = 0.1
while True:
    # send_can(msg1)
    print(msg0.data[0])
    # time.sleep(sleeptime)

    # send_can(msg0)
    # time.sleep(sleeptime)