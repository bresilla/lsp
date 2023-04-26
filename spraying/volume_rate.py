import roslibpy
import time
import can
import cantools


class Trigger():
    def __init__(self):
        self.canbus = None
        self.sleeper = 1
        self.bridge = roslibpy.Ros(host="150.140.148.140", port=2233)

        self.dbc = """VERSION ""
        BO_ 2362179474 PD_Sprayer: 14 Vector__XXX
          SG_ AppRateVolumePerTime_Set m36 : 32|32@1- (1,0) [0|2147483647] "mm³/s" Vector__XXX
        """

        self.rpa_topic = roslibpy.Topic(self.bridge, '/lspg/vol_per_area_act', 'std_msgs/Float32')
        self.pds = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("PD_Sprayer")
        # self.pds_id = 214695826
        self.pds_id = 0x1C24FFF4

    def send_topic(self, topic, message):
        topic.publish(roslibpy.Message(message))
        print(message)

    def sleep(self):
        time.sleep(self.sleeper)
    
    def recv_can(self, db, id):
        while(True):
            try:
                message = self.canbus.recv()
                if message.arbitration_id == id:
                    data = db.decode(message.data)
                    return data
            except can.CanError:
                print("MESSAGE NOT RECIEVED")
 
    def send_topic(self, topic, message):
        topic.publish(roslibpy.Message(message))
        print(message)


def main(args=None):
    trig = Trigger()

    while not trig.bridge.is_connected:
        try:
            print("BRIDGE CONNECTED")
            trig.bridge.run()
        except:
            print("BRIDGE NOT CONNECTED")
            time.sleep(5)

    while trig.canbus is None:
        try:
            # trig.canbus = can.interface.Bus(channel='vcan0', bustype='socketcan', bitrate=250000, fd=True)
            trig.canbus = can.interface.Bus(channel=2, bustype='vector', app_name="CANoe", fd=True)
            print("CAN CONNECTED")
        except:
            print("CAN NOT CONNECTED")
            time.sleep(5)

    while True:
        message = trig.recv_can(trig.pds, trig.pds_id)
        print(message["AppRateVolumePerArea_Act"])
        trig.send_topic(trig.rpa_topic, {'data': float(message["AppRateVolumePerTime_Set"])})

if __name__ == '__main__':
    main()
