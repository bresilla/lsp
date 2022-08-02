import cv2
import depthai as dai
import contextlib
import datetime
import os
import time


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

    while cpt < 100000:
        cpt += 1
        timenow = datetime.datetime.now()
        in_milisec = str(timenow.strftime("%H_%M_%S_%f"))
        for q_rgb, stream_name, date_folder in q_rgb_list:
            in_rgb = q_rgb.tryGet()
            if in_rgb is not None:
                frame = in_rgb.getCvFrame()
                cv2.imshow(stream_name, frame)
                cv2.imwrite(date_folder + "image_" + in_milisec + "_" + stream_name + "_%06i" % cpt + ".jpg", frame)
        time.sleep(0.25)
        print(in_milisec)
        print(cpt)
        print()
        if cv2.waitKey(1) == ord('q'):
            break
