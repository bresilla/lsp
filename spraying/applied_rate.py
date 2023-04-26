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
        BO_ 2362179326 PD: 8 TractorECU
          SG_ AppRateVolumePerTime_Set m36 : 32|32@1- (1,0) [0|2147483647] "mm³/s" Vector__XXX
        BO_ 2563474819 PD_Sprayer: 8 Vector__XXX
          SG_ AppRateVolumePerArea_Act m2 : 32|32@1- (0.01,0) [0|21474836.47] "mm³/m²" Vector__XXX
        """

        self.rpa_topic = roslibpy.Topic(self.bridge, '/lspg/vol_per_time_set', 'std_msgs/Float32')
        self.vpas_topic = roslibpy.Topic(self.bridge, '/lspg/vol_per_area_act', 'std_msgs/Float32')

        self.pds = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("PD")
        #self.pds_id = 0x1C24FFF4
        self.pds_id = 0xCCB8081

        self.pds_spray = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("PD_Sprayer")
        self.vpas_id = 0x18CB8583


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
            trig.bridge.run()
            print("BRIDGE CONNECTED")
        except:
            print("BRIDGE NOT CONNECTED")
            time.sleep(5)

    while trig.canbus is None:
        try:
            trig.canbus = can.interface.Bus(channel=2, bustype='vector', app_name="CANoe", fd=True)
            print("CAN CONNECTED")
        except:
            print("CAN NOT CONNECTED")
            time.sleep(5)

    while True:
       # message_arpt = trig.recv_can(trig.pds, trig.pds_id)
       # print("AppRateVolumePerTime_Set: ", message_arpt["AppRateVolumePerTime_Set"])
       # trig.send_topic(trig.rpa_topic, {'data': float(message_arpt["AppRateVolumePerTime_Set"])})

        message_arpa = trig.recv_can(trig.pds_spray, trig.vpas_id)
        print("AppRateVolumePerArea_Act: ", message_arpa["AppRateVolumePerArea_Act"])
        trig.send_topic(trig.vpas_topic, {'data': float(message_arpa["AppRateVolumePerArea_Act"])})




if __name__ == '__main__':
    main()

