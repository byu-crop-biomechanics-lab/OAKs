#!/usr/bin/env python3

# DEPTHAI_WATCHDOG_INITIAL_DELAY=60000 DEPTHAI_BOOTUP_TIMEOUT=60000 python3 test-1.py

'''
To Do

* Have less windows open
* Make sure that it captures the amount you need, not one more or one less
* catch things like only having one OAK connected. try and catch and print errors or allow one camera to run by itself

'''

import cv2
import depthai as dai
import time
import numpy as np
import os
from scipy.io import savemat

os.environ['DEPTHAI_WATCHDOG_INITIAL_DELAY'] = '60000'
os.environ['DEPTHAI_BOOTUP_TIMEOUT'] = '60000'


def clamp(num, v0, v1):
    return max(v0, min(num, v1))

# Create pipeline
def create_pipeline():
    pipeline = dai.Pipeline()

    # Create nodes
    camRgb = pipeline.create(dai.node.ColorCamera)
    xoutVideo = pipeline.create(dai.node.XLinkOut)
    
    stillEncoder = pipeline.create(dai.node.VideoEncoder)
    controlIn = pipeline.create(dai.node.XLinkIn)
    configIn = pipeline.create(dai.node.XLinkIn)
    stillMjpegOut = pipeline.create(dai.node.XLinkOut)
    
    manip = pipeline.create(dai.node.ImageManip)

    # Set stream names
    xoutVideo.setStreamName("video")
    controlIn.setStreamName('control')
    configIn.setStreamName('config')
    stillMjpegOut.setStreamName('still')

    # Properties
    camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    camRgb.setStillSize(1920, 1080) 
    camRgb.setPreviewSize(640, 360)  
    

    stillEncoder.setDefaultProfilePreset(1, dai.VideoEncoderProperties.Profile.MJPEG)

    xoutVideo.input.setBlocking(False)
    xoutVideo.input.setQueueSize(1)

    # Linking
    camRgb.preview.link(xoutVideo.input)
    camRgb.still.link(stillEncoder.input)
    controlIn.out.link(camRgb.inputControl)
    configIn.out.link(camRgb.inputConfig)
    stillEncoder.bitstream.link(stillMjpegOut.input)
    
    return pipeline

# find center and bounding rect for all pom poms in frame
detector = cv2.SimpleBlobDetector()
def blobbing(frame):
    # rgb to hsv
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # binary image from purple ranges
    purple_lower = np.array([110,50,30])
    purple_upper = np.array([135,255,255])
    purple_amount = 400
    purple_mask = cv2.inRange(frame, purple_lower, purple_upper)
    
    # get rid of noise
    kernel = np.ones((4, 4), "uint8")
    purple_mask = cv2.dilate(purple_mask, kernel)         
    
    # block anything that isn't purple
    frame = cv2.bitwise_and(frame, frame, mask=purple_mask)
    frame = cv2.cvtColor(frame,cv2.COLOR_HSV2BGR) 
    
    # Find countours and draw
    contours, hierarchy = cv2.findContours(image=purple_mask, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)
    # cv2.drawContours(image=frame, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
    
    # draw rects around objects
    centers = []
    corners = []
    for contour in contours:
        # filter small contours out
        if cv2.contourArea(contour) < 20:
            continue
        
        # get the xmin, ymin, width, and height coordinates from the contours
        (x, y, w, h) = cv2.boundingRect(contour)
        # draw the bounding boxes
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        # crop image for centroids
        x_1 = x
        x_2 = x + w
        y_1 = y
        y_2 = y + h
        corners.append([x_1,y_1,x_2,y_2])
        center_frame = purple_mask[y_1:y_2, x_1:x_2]
        
        # find centroid based on moments
        ret,thresh = cv2.threshold(center_frame,127,255,0)
        M = cv2.moments(thresh)
        cX = int(M["m10"] / M["m00"]) + x
        cY = int(M["m01"] / M["m00"]) + y
        centers.append([cX, cY])
        cv2.circle(frame, (cX, cY), 3, (255, 255, 255), -1)
        text = "centroid: " + str(cX) + " " + str(cY)
        # cv2.putText(frame, text, (cX - 25, cY - 25),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        #--- ---# 
    
    # cv2.imshow("thing", frame)
    return frame, centers, corners    
        
def analyze_batch(an_folder_name):

    an_dict_index = None
    for index, dictionary in enumerate(dictionaries):
        if dictionaries[index]["Name"] == an_folder_name:
            an_dict_index = index
    if an_dict_index == None:
        print("batch not found")
        return False
    
    print("batch found")
    for file in dictionaries[an_dict_index]["File"]:
        image = cv2.imread("Pictures/" + an_folder_name + "/" + file)
        
        manip_frame, center, box = blobbing(frame)
                
        dictionaries[an_dict_index]["N"].append(len(center))
        dictionaries[an_dict_index]["Center"].append(center)
        dictionaries[an_dict_index]["Box"].append(box)   
        
        print("analyzed " + file)
        
    savemat("Pictures/" + dictionaries[an_dict_index]["Name"] + "/" + dictionaries[an_dict_index]["Name"] + ".mat", dictionaries[an_dict_index])

    print("Batch analyzed")
        

# device_info = dai.DeviceInfo("169.254.1.222")
# device_info = dai.DeviceInfo("18443010F1C6C41200")
# device_info = dai.DeviceInfo("18443010B142C41200")

# saving images things
dictionaries = []
dict_index = -1

# camera things
pictures_1 = 1
pictures_2 = 1
capture = False
last_time = time.time()
devices = [None,None]
videos = [None, None]
controlQueues = [None, None]
configQueues = [None, None]
stillQueues = [None, None]


# camera settings
poll_time = 0.2 # timer for capturing images. in seconds.
expTime = 3500
sensIso = 3000 
EXP_STEP = 500  # us
ISO_STEP = 50

#---Loop---#
while 1:

    # show camera stream
    for index, device in enumerate(devices):
        if device != None:
            videoIn = videos[index].get()
            frame = videoIn.getCvFrame()
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        
            cv2.imshow("video " + str(index+1), frame)
            
        
    # show blank image for keystrokes
    else:
        frame = np.ones([512,512,1],dtype=np.uint8)
        cv2.imshow("blank", frame)


    # saves images every poll_time seconds
    if capture == True:  

            # If poll_time has passed
            if devices[0] == None or devices[1] == None:
                # capture = false
                pass
            else:
                if time.time() - last_time > poll_time:
                    ctrl = dai.CameraControl()
                    ctrl.setCaptureStill(True)
                    
                    # take both pictures
                    controlQueues[0].send(ctrl)
                    controlQueues[1].send(ctrl)
            
                    # save picture one
                    stillFrames = stillQueues[0].tryGetAll()
                    for stillFrame in stillFrames:
                        
                        # Read in frame to numpy array and rotate it
                        frame = cv2.imdecode(stillFrame.getData(), cv2.IMREAD_UNCHANGED)
                        frame = cv2.rotate(frame, cv2.ROTATE_180)
                        
                        # manip_frame, center, box = blobbing(frame)
                        
                        # write file to folder
                        file_name = "picture" + str(1) + "_" + str(pictures_1) + ".png"
                        status = cv2.imwrite("Pictures/" + folder_name + "/" + file_name, frame)
                        
                        # Add name to folder
                        dictionaries[dict_index]["File"].append(file_name)
                        print(dictionaries[dict_index]["File"][-1])
                        print(str(pictures_1) + " saved: " + str(status) + "\n")
                        
                        
                        pictures_1 += 1
                    
                    # capture picture two
                    stillFrames = stillQueues[1].tryGetAll()
                    for stillFrame in stillFrames:
                        
                        # Read in frame to numpy array and rotate it
                        frame = cv2.imdecode(stillFrame.getData(), cv2.IMREAD_UNCHANGED)
                        frame = cv2.rotate(frame, cv2.ROTATE_180)
                        
                        # manip_frame, center, box = blobbing(frame)
                        
                        # write file to folder
                        file_name = "picture" + str(2) + "_" + str(pictures_2) + ".png"
                        status = cv2.imwrite("Pictures/" + folder_name + "/" + file_name, frame)
                        
                        # Add name to folder
                        dictionaries[dict_index]["File"].append(file_name)
                        print(dictionaries[dict_index]["File"][-1])
                        print(str(pictures_2) + " saved: " + str(status) + "\n")
                        
                        
                        pictures_2 += 1
                    
                    # save both to folder then to dictionary
                    # make sure its picture1_1 and picture2_1
                    
                    if picture_limit != None:
                        if pictures_1 >= picture_limit:
                            capture = False
                            print("Capturing done, captured " + str(picture_limit) + " pictures.")
                            analyze_batch(dictionaries[dict_index]["Name"])
                    
                    last_time = time.time()
                            
            
            
            
    # take in keyboard input
    key = cv2.waitKey(1)
    
    
    # stop program
    if key == ord('q'):
        
        # savemat("Pictures/" + dictionaries[dict_index]["Name"] + "/" + dictionaries[dict_index]["Name"] + ".mat", dictionaries[dict_index])
        cv2.destroyAllWindows()
        for device in devices:
            device.close()
        
        break
    
    # add OAK1
    elif key == ord('g'):
        print("\nattempting OAK1 connection")
        attempts = 1
        device_info = dai.DeviceInfo("169.254.1.222")
        while attempts <= 20:
            print("\nattempt: " + str(attempts))
            try:
                devices[0] = dai.Device(device_info)
                attempts = 30
            except Exception as e:
                attempts += 1
                print(e)
        if attempts == 30:
            print("Connected to OAK 1")

            pipeline = create_pipeline()
            devices[0].startPipeline(pipeline)
            
            videos[0] = devices[0].getOutputQueue(name="video", maxSize=1, blocking=False)
            controlQueues[0] = devices[0].getInputQueue('control')
            configQueues[0] = devices[0].getInputQueue('config')
            stillQueues[0] = devices[0].getOutputQueue('still')
            
            # ctrl = dai.CameraControl()
            # ctrl.setManualExposure(expTime, sensIso)
            # controlQueues[0].send(ctrl)
            
        else:
            print("try connecting later")
            
    elif key in [ord('i'), ord('o'), ord('k'), ord('l')]:
        if key == ord('i'): expTime -= EXP_STEP
        if key == ord('o'): expTime += EXP_STEP
        if key == ord('k'): sensIso -= ISO_STEP
        if key == ord('l'): sensIso += ISO_STEP
        expTime = clamp(expTime, 1, 33000)
        sensIso = clamp(sensIso, 100, 3000)
        print("Setting manual exposure, time: ", expTime, "iso: ", sensIso)
        ctrl = dai.CameraControl()
        ctrl.setManualExposure(expTime, sensIso)
        controlQueues[0].send(ctrl)
    
    elif key == ord('a'):
        if devices[0] != None and devices[1] != None:
            ctrl = dai.CameraControl()
            ctrl.setAutoExposureEnable()
            controlQueues[0].send(ctrl)
            controlQueues[1].send(ctrl)
            print("Auto")
        else:
            print("two not connected")        
        
    # add OAK2
    elif key == ord('h'):
        print("\nattempting OAK2 connection")
        attempts = 1
        device_info = dai.DeviceInfo("169.254.1.221")
        while attempts <= 20:
            print("\nattempt: " + str(attempts))
            try:
                devices[1] = dai.Device(device_info)
                attempts = 30
            except Exception as e:
                attempts += 1
                print(e)
        if attempts == 30:
            
            pipeline = create_pipeline()
            devices[1].startPipeline(pipeline)
            
            videos[1] = devices[1].getOutputQueue(name="video", maxSize=1, blocking=False)
            controlQueues[1] = devices[1].getInputQueue('control')
            configQueues[1] = devices[1].getInputQueue('config')
            stillQueues[1] = devices[1].getOutputQueue('still')
            
            # ctrl = dai.CameraControl()
            # ctrl.setManualExposure(expTime, sensIso)
            # controlQueues[1].send(ctrl)
            
        else:
            print("try connecting later")
    
    # start saving images
    elif key == ord('c'):
        # print('c')
        
        if capture == True:
            print("Finished capturing")
            capture = False
            analyze_batch(dictionaries[dict_index]["Name"])
            
        elif capture == False:
            capture = True
            pictures = 1
            
            yesno = input("Do you have an amount of pictures to take? [Y/n] ")
            if yesno == "Y" or yesno == "y":
                picture_limit = int(input("How many do you want taken: "))
            else:
                picture_limit = None
                
            repeat = True
            while repeat == True:
                folder_name = input("Write to Folder: ")
                exists = os.path.exists("Pictures/" + folder_name)
                # if not exists:
                #     os.mkdir("Pictures/" + folder_name)
                #     dict_index +=1
                #     repeat = False
                if exists:
                    print("This folder already exists")
                else:
                    repeat = False
            os.mkdir("Pictures/" + folder_name)
            dict_index +=1
                                          
                
            dictionaries.append({"Name": folder_name, "File":[], "N":[], "Center":[], "Box":[]})
            
            
        # print(capture)
