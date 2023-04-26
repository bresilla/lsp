import argparse
import roslibpy
import time


class Trigger():
    def __init__(self):
        self.sleeper = 1
        self.bridge = roslibpy.Ros(host="10.147.17.52", port=2233)
        self.trigger = roslibpy.Topic(self.bridge, "/lspn/trigger_flag", 'std_msgs/Bool')

    def send_topic(self, topic, message):
        topic.publish(roslibpy.Message(message))
        print(message)

    def sleep(self):
        time.sleep(self.sleeper)


def main(args=None):
    trig = Trigger()

    while not trig.bridge.is_connected:
        try:
            print("BRIDGE CONNECTED")
            trig.bridge.run()
        except:
            time.sleep(5)
            print("BRIDGE NOT CONNECTED")

    while True:
        trig.send_topic(trig.trigger, {'data': True})
        trig.sleep()


if __name__ == '__main__':
    main()
