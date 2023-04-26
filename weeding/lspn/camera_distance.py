import cv2
import depthai as dai
import contextlib
import datetime
import os
import time
import numpy as np
import matplotlib.pyplot as plt
from haversine import haversine


class Kinematics():
    def __init__(self):
        self.iters = 5
        self.canbus = None
        self.dbc = """VERSION ""
        BO_ 2365475321 GBSD: 8 Vector__XXX
         SG_ GroundBasedMachineSpeed : 0|16@1+ (0.001,0) [0|64.255] "m/s" Vector__XXX
        BO_ 2314732030 GNSSPositionRapidUpdate: 8 Bridge
         SG_ Longitude : 32|32@1- (1E-007,0) [-180|180] "deg" Vector__XXX
         SG_ Latitude : 0|32@1- (1E-007,0) [-90|90] "deg" Vector__XXX
        """

        self.gbsd_id = 217991673
        self.gbsd = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("GBSD")
        self.gnss_id = 167248382
        self.gnss = cantools.db.load_string(self.dbc, 'dbc').get_message_by_name("GNSSPositionRapidUpdate")

    def recv_can(self, db, id, description):
        data = None
        for e in range(10):
            try:
                message = self.canbus.recv()
                if message.arbitration_id == id:
                    data = db.decode(message.data)
                    break
            except can.CanError:
                print("MESSAGE NOT RECIEVED")
        if data == None: print("MESSAGE ", description, " NOT AVALIABLE")
        return data
    
kin = Kinematics()
try:
    kin.canbus = can.interface.Bus(channel='vcan0', bustype='socketcan')
    print("CAN CONNECTED")
except:
    print("CAN NOT CONNECTED")
    exit()

prev = None
dist = 0

def counter(img, display, title):
    y, x = int(img.shape[0]/2), 0
    h, w = 50, img.shape[1]
    roi = img[y:y+h, x:x+w]
    img = roi

    img = cv2.GaussianBlur(img, (9, 9), 0)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    bound_lower = np.array([30, 30, 0])
    bound_upper = np.array([90, 255, 255])

    mask_green = cv2.inRange(hsv_img, bound_lower, bound_upper)

    kernel = np.ones((7,7),np.uint8)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_CLOSE, kernel)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)
    mask_green = cv2.dilate(mask_green, kernel, iterations=1)
    mask_green = cv2.erode(mask_green, kernel, iterations=1)

    seg_img = cv2.bitwise_and(img, img, mask=mask_green)
    gray_image = cv2.cvtColor(seg_img, cv2.COLOR_BGR2GRAY)
    num_white_pixels = cv2.countNonZero(gray_image)

    if display:
        cv2.imshow(title, seg_img)
        cv2.waitKey(1)

    return seg_img, num_white_pixels

def blober(img, display, title):
    y, x = int(img.shape[0]/2), 0
    h, w = 150, img.shape[1]
    roi = img[y:y+h, x:x+w]
    img = roi

    img = cv2.GaussianBlur(img, (9, 9), 0)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    bound_lower = np.array([30, 30, 0])
    bound_upper = np.array([90, 255, 255])

    mask_green = cv2.inRange(hsv_img, bound_lower, bound_upper)

    kernel = np.ones((7,7),np.uint8)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_CLOSE, kernel)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)
    mask_green = cv2.dilate(mask_green, kernel, iterations=1)
    mask_green = cv2.erode(mask_green, kernel, iterations=1)

    seg_img = cv2.bitwise_and(img, img, mask=mask_green)
    contours, hier = cv2.findContours(mask_green.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = 1000
    large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

    for e in large_contours:
        moments = cv2.moments(e)
        if moments["m00"] != 0:
            x = int(moments["m10"] / moments["m00"])
            y = int(moments["m01"] / moments["m00"])
            cv2.circle(seg_img, (x, y), 5, (0, 255, 0), -1)

    output = cv2.drawContours(seg_img, large_contours, -1, (0, 0, 255), 3)
    if display:
        cv2.imshow(title, seg_img)
        cv2.waitKey(1)
    return output, seg_img


if os.name == 'nt': 
    sep = "\\"
    base_folder = "D:\\Cam\\"
else:
    sep = "/"
    base_folder = "/home/bresilla/depthai/vid" 

timenow = datetime.datetime.now()
folder_name = base_folder + sep + str(timenow.strftime("%Y%m%d")) + sep



# This can be customized to pass multiple parameters
def getPipeline(device_type):
    pipeline = dai.Pipeline()
    cam_rgb = pipeline.create(dai.node.ColorCamera)
    cam_rgb.setPreviewSize(1920, 1080)
    cam_rgb.setBoardSocket(dai.CameraBoardSocket.RGB)
    cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    cam_rgb.setInterleaved(False)

    xout_rgb = pipeline.create(dai.node.XLinkOut)
    xout_rgb.setStreamName("rgb")
    cam_rgb.preview.link(xout_rgb.input)
    return pipeline

q_rgb_list = []
cpt = 0

# def plot_graph(list_of_points: list):
#     plt.figure(figsize=(15, 10), linewidth=2, edgecolor='steelblue', facecolor='skyblue')
#     plt.subplots_adjust(left=0.20, bottom=0.20)
#     ax = plt.gca()
#     ax.set_xlim([0, max_x])
#     plt.plot(list_of_points, label="Points")
#     plt.legend()
#     plt.show()

with contextlib.ExitStack() as stack:
    device_infos = dai.Device.getAllAvailableDevices()
    if len(device_infos) == 0:
        raise RuntimeError("No devices found!")
    else:
        print("Found", len(device_infos), "devices")

    for device_info in device_infos:
        openvino_version = dai.OpenVINO.Version.VERSION_2021_4
        device = stack.enter_context(dai.Device(openvino_version, device_info, False))
        stream_name = device.getMxId()
        device_type = "OAK-D-POE"
        pipeline = getPipeline(device_type)
        device.startPipeline(pipeline)

        q_rgb = device.getOutputQueue(name="rgb", maxSize=1, blocking=False)
        date_folder = folder_name + stream_name + sep
        if not os.path.exists(date_folder): os.makedirs(date_folder)

        q_rgb_list.append((q_rgb, stream_name, date_folder))

    while True:
        gnss_message = kin.recv_can(kin.gnss, kin.gnss_id, "GNSS")
        print("--------------------------------------------------")
        if gnss_message != None:
            lon=gnss_message["Longitude"]
            lat=gnss_message["Latitude"]
            if prev is None:
                prev = [lat, lon]
                continue
            delta=haversine((prev[0], prev[1]), (lat, lon))
            dist = dist + delta
            prev = [lat, lon]
            print(dist*1000)

        cpt += 1
        timenow = datetime.datetime.now()
        in_milisec = str(timenow.strftime("%H_%M_%S_%f"))
        for q_rgb, stream_name, date_folder in q_rgb_list:
            in_rgb = q_rgb.tryGet()
            if in_rgb is not None:
                frame = in_rgb.getCvFrame()
                _, pixels = counter(frame, True, stream_name)
                txtfile = date_folder + "__" + stream_name + ".csv"
                with open(txtfile, "a") as f: f.write(f"{in_milisec}, {dist} ,{pixels}\n")
                cv2.imshow(stream_name, frame)
                cv2.imwrite(date_folder + "image_" + in_milisec + "_" + stream_name + "_%06i" % cpt + ".jpg", frame)
        time.sleep(0.25)
        print(in_milisec)
        print(cpt)
        print()
        if cv2.waitKey(1) == ord('q'):
            break