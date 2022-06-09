import os
import time
import can
import cantools
import roslibpy


class Kinematics():
    def __init__(self):
        self.sleeper = 1
        self.canbus = None
        self.bridge = roslibpy.Ros(host="150.140.148.140", port=2233)
        #self.bridge = roslibpy.Ros(host="10.42.0.1", port=9090)
        self.dbc = """VERSION ""
        BO_ 2365475321 GBSD: 8 Vector__XXX
         SG_ GroundBasedMachineSpeed : 0|16@1+ (0.001,0) [0|64.255] "m/s" Vector__XXX
        BO_ 2314732030 GNSSPositionRapidUpdate: 8 Bridge
         SG_ Longitude : 32|32@1- (1E-007,0) [-180|180] "deg" Vector__XXX
         SG_ Latitude : 0|32@1- (1E-007,0) [-90|90] "deg" Vector__XXX
        BO_ 2362179326 PD: 14 Vector__XXX
         SG_ AppRateVolumePerArea_Act m2 : 32|32@1- (0.01,0) [0|21474836.47] "mm³/m²" Vector__XXX
         SG_ AppRateVolumePerTime_Set m36 : 32|32@1- (1,0) [0|2147483647] "mm³/s" Vector__XXX
         SG_ AppRateVolumePerTime_Act m37 : 32|32@1- (1,0) [0|2147483647] "mm³/s" Vector__XXX
        """

        self.gbsd = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("GBSD")
        self.gnss = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("GNSSPositionRapidUpdate")
        self.pd = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("PD")

        self.speed_topic = roslibpy.Topic(self.bridge, '/lsp3/speed', 'std_msgs/Float32')
        self.longitude_topic = roslibpy.Topic(self.bridge, '/lsp3/longitude', 'std_msgs/Float32')
        self.latitude_topic = roslibpy.Topic(self.bridge, '/lsp3/latitude', 'std_msgs/Float32')
        self.odometry_topic = roslibpy.Topic(self.bridge, '/lsp3/odometry', 'nav_msgs/Odometry')


        self.vpaa_topic = roslibpy.Topic(self.bridge, '/lsp3/vol_per_area_act', 'std_msgs/Float32')
        self.vpts_topic = roslibpy.Topic(self.bridge, '/lsp3/vol_per_time_set', 'std_msgs/Float32')
        self.vpta_topic = roslibpy.Topic(self.bridge, '/lsp3/vol_per_time_act', 'std_msgs/Float32')

    def send_can(self, message):
        try:
            self.canbus.send(message)
        except can.CanError:
            print("COULD NOT SEND THE MESSAGE")
        print(message)

    def recv_can(self, db):
        data = None
        try:
            message = self.canbus.recv()
            data = db.decode(message.data)
        except can.CanError:
            print("MESSAGE NOT RECIEVED")
        return data

    def send_topic(self, topic, message):
        topic.publish(roslibpy.Message(message))
        print(message)
 
    def sleep(self):
        time.sleep(self.sleeper)


def main(args=None):
    kin = Kinematics()

    while kin.canbus is None:
        try:
            print("CAN CONNECTED")
            if os.name == 'nt':
                kin.canbus = can.interface.Bus(channel=3, bustype='vector', app_name="CANoe")
            else:
                kin.canbus = can.interface.Bus(channel='vcan0', bustype='socketcan')
        except:
            print("CAN NOT CONNECTED")
            time.sleep(5)

    while not kin.bridge.is_connected:
        try:
            print("BRIDGE CONNECTED")
            kin.bridge.run()
        except:
            print("BRIDGE NOT CONNECTED")
            time.sleep(5)

    while True:
        gnss_message = kin.recv_can(kin.gnss)
        gbsd_message = kin.recv_can(kin.gbsd)
        pd_message = kin.recv_can(kin.pd)

        kin.send_topic(kin.speed_topic, {'data': float(gbsd_message["GroundBasedMachineSpeed"])})
        kin.send_topic(kin.longitude_topic, {'data': float(gnss_message["Longitude"])})
        kin.send_topic(kin.latitude_topic, {'data': float(gnss_message["Latitude"])})
        kin.send_topic(kin.vpaa_topic, {'data': float(gnss_message["AppRateVolumePerArea_Act"])})
        kin.send_topic(kin.vpts_topic, {'data': float(gnss_message["AppRateVolumePerTime_Set"])})
        kin.send_topic(kin.vpta_topic, {'data': float(gnss_message["AppRateVolumePerTime_Act"])})
        kin.send_topic(kin.odometry_topic, {
            "pose": {
                "pose": {
                    "position": {"x": float(gnss_message["Longitude"]), "y": float(gnss_message["Latitude"])}
                }
            },
            "header": {"frame_id": "odom"}
        })
        # kin.sleep()


if __name__ == '__main__':
    main()
