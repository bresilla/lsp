import argparse
import roslibpy
import time


class Trigger():
    def __init__(self):
        self.sleeper = 1
        self.bridge = roslibpy.Ros(host="150.140.148.140", port=2233)
        self.trigger = roslibpy.Topic(self.bridge, "/lsp3/trigger_flag", 'std_msgs/Bool')

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
            print("BRIDGE NOT CONNECTED")
            time.sleep(5)

    while True:
        trig.send_topic(trig.trigger, {'data': False})
        trig.sleep()


if __name__ == '__main__':
    main()
