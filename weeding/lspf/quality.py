import serial
import can
import cantools
import time
import os
import roslibpy

if os.name == 'nt': 
    filename = "C:\\R4CLogs\\Sensors\\" + time.strftime('%y%m%d%H%M%S', time.localtime(time.time())) + ".txt"
else:
    filename = "/home/bresilla/logs/"  + time.strftime('%y%m%d%H%M%S', time.localtime(time.time())) + ".txt"

dbc = """VERSION ""
BO_ 2365194522 PD_Loader: 8 SEND
  SG_ Quality : 0|32@1+ (1,0) [0|100] "%"  Loader
BO_ 2566834709 DM1: 8 SEND
  SG_ FlashRedStopLamp : 12|2@1+ (1,0) [0|3] "" Vector__XXX
  SG_ FlashAmberWarningLamp : 10|2@1+ (1,0) [0|3] "" Vector__XXX
"""
 
if os.name == 'nt':
    ser = serial.Serial('COM13', 9600)
    bus = can.interface.Bus(channel=0, bustype='vector', app_name="CANoe")
else:
    ser = serial.Serial('/dev/ttyACM0', 9600)
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

pdl = cantools.db.load_string(dbc, 'dbc').get_message_by_name("PD_Loader")
dm1 = cantools.db.load_string(dbc, 'dbc').get_message_by_name("DM1")

bridge = roslibpy.Ros(host="150.140.148.140", port=2233)
sensor_topic = roslibpy.Topic(bridge, '/lspf/sensors', 'std_msgs/Int16MultiArray')
sensor_frequency_topic = roslibpy.Topic(bridge, '/lspf/sensors_frequency', 'std_msgs/Float32MultiArray')
quality_topic = roslibpy.Topic(bridge, '/lspf/quality', 'std_msgs/Int16')
while not bridge.is_connected:
    try:
        bridge.run()
        print("BRIDGE CONNECTED")
    except:
        print("BRIDGE NOT CONNECTED")
        time.sleep(5)


def send2can(message):
#    print(can.bus.BusState)
   try:
       bus.send(message)
    #    print(message)
   except can.CanError:
       print("COULD NOT SEND THE MESSAGE")

def send_topic(topic, message):
    topic.publish(roslibpy.Message(message))
    print(message)

prev_value = [0, 0, 0, 0]
start_time = [0, 0, 0, 0]
frequency = [0, 0, 0, 0]
counter = 0
counters = [0, 0, 0, 0]
buffer = 0
quality = 100

while True:
    buffer += 1
    data = ser.readline().decode().strip()
    splited = data.split(":")
    sensors = [int(x) for x in splited]
    result = [1 if x > 500 else 0 for x in sensors]
    send_topic(sensor_topic, {'data': result})
    with open(filename, 'a') as txt: txt.write(f"{time.time()}, {result}\n")
    for index, sensor in enumerate(result):
        if sensor != prev_value[index]:
            current_time = time.time()
            curr_frequency = (counters[index] + 1) / (current_time - start_time[index])
            print("Frequency of change:", curr_frequency, "Hz")
            frequency[index] = curr_frequency
            prev_value[index] = sensor
            start_time[index] = current_time
            counters[index] = 0
            quality = quality + 2 if quality < 100 else 100
        else:
            counters[index] += 1
            if counters[index] >= 200 * 4:
                frequency[index] = 0
                start_time[index] = 0
                counters[index] = 0
                quality = quality - 1 if quality > 0 else 0
    send_topic(sensor_frequency_topic, {'data': frequency})
    send2can(can.Message(arbitration_id=pdl.frame_id, data=pdl.encode({'Quality': quality})))
    send_topic(quality_topic, {'data': quality})
    # print(quality)
    if buffer < 50:
        send2can(can.Message(arbitration_id=dm1.frame_id, data=dm1.encode({'FlashAmberWarningLamp': 0, 'FlashRedStopLamp': 1})))
        continue