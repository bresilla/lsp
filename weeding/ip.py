import time
import socket
import roslibpy

class GetIP():
    def __init__(self):
        self.sleeper = 1
        self.bridge = roslibpy.Ros(host="150.140.148.140", port=2233)
        #self.bridge = roslibpy.Ros(host="10.42.0.1", port=9090)
        self.ip = roslibpy.Topic(self.bridge, "/lsp1/ip", 'std_msgs/String')

    def send_topic(self, topic, message):
        topic.publish(roslibpy.Message(message))
        print(message)

    def sleep(self):
        time.sleep(self.sleeper)

    def extract_ip(self):
        st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            st.connect(('10.255.255.255', 1))
            IP = st.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            st.close()
        return IP


def main(args=None):
    trig = GetIP()

    while not trig.bridge.is_connected:
        try:
            print("BRIDGE CONNECTED")
            trig.bridge.run()
        except:
            print("BRIDGE NOT CONNECTED")
            time.sleep(5)

    while True:
        trig.send_topic(trig.ip, {'data': trig.extract_ip()})
        trig.sleep()


if __name__ == '__main__':
    main()
