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
BO_ 2365475321 GBSD: 8 Vector__XXX
  SG_ GroundBasedMachineSpeed : 0|16@1+ (0.001,0) [0|64.255] "m/s" Vector__XXX
BO_ 2314732030 GNSSPositionRapidUpdate: 8 Bridge
  SG_ Longitude : 32|32@1- (1E-007,0) [-180|180] "deg" Vector__XXX
  SG_ Latitude : 0|32@1- (1E-007,0) [-90|90] "deg" Vector__XXX
"""
 
if os.name == 'nt':
    ser = serial.Serial('COM13', 9600)
    bus = can.interface.Bus(channel=0, bustype='vector', app_name="CANoe")
else:
    ser = serial.Serial('/dev/ttyACM0', 9600)
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

pdl = cantools.db.load_string(dbc, 'dbc').get_message_by_name("PD_Loader")

gbsd_id = 0xCFE49F0
gbsd = cantools.db.load_string(dbc, 'dbc').get_message_by_name("GBSD")
gnss_id = 0x9F8011C
gnss = cantools.db.load_string(dbc, 'dbc').get_message_by_name("GNSSPositionRapidUpdate")

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


def recv_can(db, id,description, tries=50):
    data = None
    i = 0
    while(i < tries):
        i = i + 1
        try:
            message = bus.recv()
            if message.arbitration_id == id:
                data = db.decode(message.data)
                print(description, data)
        except can.CanError:
            print("MESSAGE NOT RECIEVED")
    if data == None: print("MESSAGE ", description, " NOT AVALIABLE")
    return data

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

num_sensors = 2

while True:
    gnss_message = recv_can(gnss, gnss_id, "GNSS")
    gbsd_message = recv_can(gbsd, gbsd_id, "GBSD")

    buffer += 1
    data = ser.readline().decode().strip()
    splited = data.split(":")
    sensors = [int(x) for x in splited]
    result = [1 if x > 500 else 0 for x in sensors]
    send_topic(sensor_topic, {'data': result})
    with open(filename, 'a') as txt: txt.write(f"{time.time()}, {result}\n")
    for index, sensor in enumerate(result):
        if index >= num_sensors: break
        if sensor != prev_value[index]:
            current_time = time.time()
            curr_frequency = (counters[index] + 1) / (current_time - start_time[index])
            print(f"Frequency of change {index}:", curr_frequency, "Hz")
            frequency[index] = curr_frequency
            prev_value[index] = sensor
            start_time[index] = current_time
            counters[index] = 0
            quality = quality + 5 if quality < 95 else 100
        else:
            counters[index] += 1
            if counters[index] >= 200 * 10:
                frequency[index] = 0
                start_time[index] = 0
                counters[index] = 0
                quality = quality - 1 if quality > 0 else 0
    send_topic(sensor_frequency_topic, {'data': frequency})
    send2can(can.Message(arbitration_id=pdl.frame_id, data=pdl.encode({'Quality': quality})))
    send_topic(quality_topic, {'data': quality})
    # print(quality)
    # if buffer < 50:
    #     send2can(can.Message(arbitration_id=dm1.frame_id, data=dm1.encode({'FlashAmberWarningLamp': 0, 'FlashRedStopLamp': 1})))
    #     continue