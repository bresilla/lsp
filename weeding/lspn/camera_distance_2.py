import cv2
import depthai as dai
import contextlib
import datetime
import os
import time
import can
import cantools
from haversine import haversine
import json

if os.name == 'nt': 
    sep = "\\"
    base_folder = "D:\\Cam\\"
else:
    sep = "/"
    base_folder = "/home/bresilla/depthai/vid" 

if os.name == 'nt':
    bus = can.interface.Bus(channel=0, bustype='vector', app_name="CANoe")
else:
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

can_ids = [217991673, 167248382]

filters = []
for can_id in can_ids:
    filter = can.Filter(
        can_id=can_id,
        can_mask= 0x1FFFFFFF,
        extended_id=True
    )
    filters.append(filter)

# bus.set_filters(filters)

dbc = """VERSION ""
BO_ 2365475321 GBSD: 8 Vector__XXX
  SG_ GroundBasedMachineSpeed : 0|16@1+ (0.001,0) [0|64.255] "m/s" Vector__XXX
BO_ 2314732030 GNSSPositionRapidUpdate: 8 Bridge
  SG_ Longitude : 32|32@1- (1E-007,0) [-180|180] "deg" Vector__XXX
  SG_ Latitude : 0|32@1- (1E-007,0) [-90|90] "deg" Vector__XXX
"""

gbsd_id = 217991673
gbsd = cantools.db.load_string(dbc, 'dbc').get_message_by_name("GBSD")
gnss_id = 167248382
gnss = cantools.db.load_string(dbc, 'dbc').get_message_by_name("GNSSPositionRapidUpdate")

def recv_can(db, id, description):
    data = None
    for e in range(10):
        try:
            message = bus.recv()
            if message.arbitration_id == id:
                data = db.decode(message.data)
                break
        except can.CanError:
            print("MESSAGE NOT RECIEVED")
    if data == None: print("MESSAGE ", description, " NOT AVALIABLE")
    return data

timenow = datetime.datetime.now()
folder_name = base_folder + sep + str(timenow.strftime("%Y%m%d%H%M%S")) + sep

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

with contextlib.ExitStack() as stack:
    device_infos = dai.Device.getAllAvailableDevices()
    if len(device_infos) == 0:
        raise RuntimeError("No devices found!")
    else:
        print("Found", len(device_infos), "devices")

    for device_info in device_infos:
        openvino_version = dai.OpenVINO.Version.VERSION_2021_4
        device = stack.enter_context(dai.Device(openvino_version, device_info, False))
        mxid = device.getMxId()
        device_type = "OAK-D-POE"
        pipeline = getPipeline(device_type)
        device.startPipeline(pipeline)

        q_rgb = device.getOutputQueue(name="rgb", maxSize=1, blocking=False)
        stream_name = "RGB-" + mxid

        date_folder = folder_name + stream_name + sep
        if not os.path.exists(date_folder): os.makedirs(date_folder)

        q_rgb_list.append((q_rgb, stream_name, date_folder))

    while True:
        cpt += 1
        timenow = datetime.datetime.now()
        for q_rgb, stream_name, date_folder in q_rgb_list:
            in_rgb = q_rgb.tryGet()
            if in_rgb is not None:
                unix_stamp = time.time()

                gnss_message = recv_can(gnss, gnss_id, "GNSS")
                if gnss_message != None:
                    lon=gnss_message["Longitude"]
                    lat=gnss_message["Latitude"]
                    texty = date_folder + "{}".format(unix_stamp) + ".json"
                    datajson = {
                        "LON": lon,
                        "LAT": lat,
                        "TIME": unix_stamp
                    }
                    with open(texty, 'w') as file:
                        json.dump(datajson, file)
                    if prev is None:
                        prev = [lat, lon]
                    delta=haversine((prev[0], prev[1]), (lat, lon))
                    dist = dist + delta
                    prev = [lat, lon]
                        
                frame = in_rgb.getCvFrame()
                cv2.imshow(stream_name, frame)

                _, pixels = counter(frame, True, stream_name)
                txtfile = date_folder + "__" + stream_name + ".csv"
                with open(txtfile, "a") as f: f.write(f"{unix_stamp}, {dist} ,{pixels}\n")

                pathy = date_folder + "{}".format(unix_stamp) + ".jpg"
                # pathy = date_folder + "{}".format(unix_stamp) + "_%06i" % cpt + ".jpg"
                cv2.imwrite(pathy, frame)
        time.sleep(0.05)
        print(cpt)
        print()
        if cv2.waitKey(1) == ord('q'):
            break