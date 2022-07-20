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
        """

        self.gbsd_id = 0x0CFE49F0
        self.gbsd = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("GBSD")
        self.gnss_id = 0x09F8011C
        self.gnss = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("GNSSPositionRapidUpdate")

        self.speed_topic = roslibpy.Topic(self.bridge, '/lsp1/speed', 'std_msgs/Float32')
        self.longitude_topic = roslibpy.Topic(self.bridge, '/lsp1/longitude', 'std_msgs/Float32')
        self.latitude_topic = roslibpy.Topic(self.bridge, '/lsp1/latitude', 'std_msgs/Float32')
        self.odometry_topic = roslibpy.Topic(self.bridge, '/lsp1/odometry', 'nav_msgs/Odometry')

    def send_can(self, message):
        try:
            self.canbus.send(message)
        except can.CanError:
            print("COULD NOT SEND THE MESSAGE")
        print(message)

    def recv_can(self, db, id):
        data = None
        while(data == None):
            try:
                message = self.canbus.recv()
                if message.arbitration_id == id:
                    data = db.decode(message.data)
            except can.CanError:
                print("MESSAGE NOT RECIEVED")
        print(data)
        return data

    def recv_raw_can(self, id):
        data = None
        while(data == None):
            try:
                message = self.canbus.recv()
                if message.arbitration_id == id:
                    data = message
            except can.CanError:
                print("MESSAGE NOT RECIEVED")
        print(data)
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
            if os.name == 'nt':
                kin.canbus = can.interface.Bus(channel=2, bustype='vector', app_name="CANoe")
            else:
                kin.canbus = can.interface.Bus(channel='vcan0', bustype='socketcan')
            print("CAN CONNECTED")
        except:
            print("CAN NOT CONNECTED")
            time.sleep(5)

    while not kin.bridge.is_connected:
        try:
            kin.bridge.run()
            print("BRIDGE CONNECTED")
        except:
            print("BRIDGE NOT CONNECTED")
            time.sleep(5)

    while True:
        gnss_message = kin.recv_can(kin.gnss, kin.gnss_id)
        gbsd_message = kin.recv_can(kin.gbsd, kin.gbsd_id)

        print("---")

        kin.send_topic(kin.speed_topic, {'data': float(gbsd_message["GroundBasedMachineSpeed"])})
        kin.send_topic(kin.longitude_topic, {'data': float(gnss_message["Longitude"])})
        kin.send_topic(kin.latitude_topic, {'data': float(gnss_message["Latitude"])})
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
