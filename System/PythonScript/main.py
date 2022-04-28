import os
from threading import Thread
import cv2
import numpy as np
import time
import multiprocessing
from skimage import data, feature
from keras.models import Sequential
from keras.layers import Dense
from keras.models import model_from_json
import boto3
import requests
import sys
import getopt

class Utilities:
    def findObjects(self, mOutputs, THRESH, SUP_THRESH):
        boundingBoxLocations = []
        classes = []
        confidence = []
        for output in mOutputs:
            for prediction in output:
                classProbs = prediction[5:]
                class_id = np.argmax(classProbs)
                conf = classProbs[class_id]
                if conf > THRESH:
                    w, h = int(prediction[2] * 320), int(prediction[3] * 320)
                    x, y = int((prediction[0] * 320) - w / 2), int((prediction[1] * 320) - h / 2)
                    boundingBoxLocations.append([x, y, w, h])
                    confidence.append(float(conf))
                    classes.append(class_id)
        boxesToKeep = cv2.dnn.NMSBoxes(boundingBoxLocations, confidence, THRESH, SUP_THRESH, )
        return boxesToKeep, boundingBoxLocations, classes, confidence

    def showDetectedImages(self, img, boundingBoxIDs, allBoundingBoxes, classIDs, confidenceVals, widthR, heightR):
        finalLocations = []
        for i in boundingBoxIDs:
            box = allBoundingBoxes[i]
            x, y, w, h = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            x = int(x * widthR)
            y = int(y * heightR)
            w = int(w * widthR)
            h = int(h * heightR)
            if classIDs[i] == 0:
                classWithConf = 'Person - ' + str(int(confidenceVals[i] * 100)) + '%'
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 10)
                cv2.putText(img, classWithConf, (x + 5, y - 10), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 0))
                finalLocations.append([x, y, w, h])
        return finalLocations

    def YOLO(self, frame, THRESH, SUP_THRESH):
        originalW, originalH = frame.shape[1], frame.shape[0]

        neuralNetwork = cv2.cv2.dnn.readNetFromDarknet('yolov3.cfg', 'yolov3.weights')
        neuralNetwork.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        neuralNetwork.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

        blob = cv2.dnn.blobFromImage(frame, 1 / 255, (320, 320), True, crop=False)
        neuralNetwork.setInput(blob)
        layerNames = neuralNetwork.getLayerNames()
        outputNames = [layerNames[index - 1] for index in neuralNetwork.getUnconnectedOutLayers()]
        outputs = neuralNetwork.forward(outputNames)

        predictedObjects, bBoxLocations, classIDs, convValues = self.findObjects(self, outputs, THRESH, SUP_THRESH)
        finalLocationsInFrame = self.showDetectedImages(self, frame, predictedObjects, bBoxLocations, classIDs, convValues, originalW / 320, originalH / 320)
        return finalLocationsInFrame

    def sendLocationsToDB(self, studentNumber, classInstance, X, Y, W, H):
        url = "http://192.168.1.11:5000/api/user/add_students_locations"
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        data = {
            "student_number": studentNumber,
            "exam_instance_id": classInstance,
            "x": X,
            "y": Y,
            "w": W,
            "h": H
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("JSON Response ", response.json()['status'])
            if response.json()['status'] != 'success':
                print("An error has occured")
            else:
                print("student added successfully")

class ProcessingStudent:
    def __init__(self, locations, sensitivity, classInstance):
        self.locations = locations
        self.sensitivity = sensitivity
        self.classInstance = classInstance
        self.cheatingInstance = []
        for l in range(len(self.locations)):
            self.cheatingInstance.append(1)

        # json_file = open('model.json', 'r')
        # loaded_model_json = json_file.read()
        # json_file.close()
        # self.loaded_model = model_from_json(loaded_model_json)
        # self.loaded_model.load_weights("model.h5")
        # self.loaded_model.compile(loss = 'categorical_crossentropy', optimizer= 'adam', metrics = ['accuracy'])

    def hog(self, image):
        hogImage = cv2.resize(image, (256, 256))
        hogImage = cv2.cvtColor(hogImage, cv2.COLOR_RGB2GRAY)
        hogVector, hogImage = feature.hog(hogImage, orientations=9, pixels_per_cell=(8, 8), cells_per_block=(2, 2), block_norm='L2', visualize=True)
        return hogImage

    def sendToDB(self, filePath, fileName):
        client = boto3.client('s3', aws_access_key_id='AKIAWKAZELKAIHEHAREM', aws_secret_access_key='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')
        bucket = 'classroommonitoring'
        bucket_file_path = str(fileName)
        client.upload_file(filePath, bucket, bucket_file_path, ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/jpeg'})

    def imwriteToJPG(self, image, classInstance, studentNumber, studentsCheatingInstance):
        fileName = "c" + str(studentsCheatingInstance) + "-" + classInstance + "-" + str(studentNumber) + ".jpg"
        cv2.imwrite(fileName, image)
        studentsCheatingInstance = studentsCheatingInstance + 1
        return fileName, studentsCheatingInstance

    def predict(self, frames, studentNumber, X, Y, W, H):
        confValues = []
        for frame in frames:
            studentCrop = frame[int(Y - H / 2): int(Y - H / 2 + H), int(X - W / 2): int(X - W / 2 + W)]
            hogImage = self.hog(studentCrop)
        #     confValues.append(np.argmax(self.loaded_model.predict(hogImage)))  #check this line again after training
        #
        # q75, q25 = np.percentile(confValues, [75, 25])
        # iqr = q75 - q25
        # low = q25 - (1.5 * iqr)
        # up = q75 + (1.5 * iqr)
        # filteredConfValues = []
        # filteredConfIndeces = []
        #
        # for i in confValues:
        #     if (i >= low) and (i <= up):
        #         filteredConfValues.append(i)
        #         filteredConfIndeces.append(confValues.index(i))
        #
        # avgConf = np.average(filteredConfValues)
        #
        # if(avgConf >= self.sensitivity):
        #     fileName, self.cheatingInstance[studentNumber] = self.imwriteToJPG(frames[filteredConfIndeces[np.argmax(filteredConfValues)]], self.classInstance, studentNumber + 1, self.cheatingInstance[studentNumber])
        #     self.sendToDB(fileName, fileName)
        frame = frames[0]
        studentCrop = frame[int(Y - H / 2): int(Y - H / 2 + H), int(X - W / 2): int(X - W / 2 + W)]
        fileName, self.cheatingInstance[studentNumber] = self.imwriteToJPG(studentCrop, self.classInstance, studentNumber + 1, self.cheatingInstance[studentNumber])
        self.sendToDB(fileName, fileName)


    def runThreading(self, frames):
        studentThreads = []
        for l in self.locations:
            t = Thread(target = self.predict, args=(frames, self.locations.index(l), l[0], l[1], l[2], l[3]))
            t.start()
            studentThreads.append(t)

        for st in studentThreads:
            st.join()

    def runSequential(self, frames):
        for l in self.locations:
            self.predict(frames, self.locations.index(l), l[0], l[1], l[2], l[3])

########################################################################################################################
frameRate = None
sensitivity = None
classInstanceID = None
########################################################################################################################
utils = Utilities

YOLO_THRESH = 0.2
YOLO_SUPPRESSION_THRESH = 0.4

feedEnd = False
allImages = []
frameCount = 0

def retrieveFrames(source):
    global feedEnd
    cap = cv2.VideoCapture(source)
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == True:
            allImages.append(frame)
        else:
            break
    feedEnd = True;
    print("done")

def yolo2sec():
    global frameCount
    start_time = time.time()
    maxLocations = utils.YOLO(Utilities, allImages[frameCount], YOLO_THRESH, YOLO_SUPPRESSION_THRESH)
    frameCount = frameCount + 1
    print("--- %s seconds ---" % (time.time() - start_time))
    return maxLocations, frameCount


def examVariables():
    """@brief: This function is responsible for retrieving sensitivity, exam instance id & fps"""
    sensitivity_arg = None
    exam_instance_id_arg = None
    fps = None
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, 's:e:')
    except getopt.GetoptError as e:
        # Print a message or do something useful
        print(e)
        print('Something went wrong!')
        sys.exit(2)

    ## getting arguments from the frontend
    # -s -> Sensitivity
    # -e -> exam instance id
    for option, argument in opts:
        # if the option is sensitivity
        if option == '-s':
            sensitivity_arg = argument

        # if the option is exam_instance_id
        if option == '-e':
            exam_instance_id_arg = argument

    exam_id_temp = exam_instance_id_arg
    # getting the fps value
    response = requests.get(f"http://classroommonitoring.herokuapp.com/api/user/get_fps/{exam_id_temp}")
    fps = response.json()['data']

    return sensitivity_arg, fps, exam_instance_id_arg

########################################################################################################################
########################################################################################################################

if __name__ == "__main__":
    sensitivity, frameRate, classInstanceID = examVariables()
    gatherFrames = Thread(target = retrieveFrames, args = ("/Users/marwanawad1/Desktop/HM_1.mp4",) )
    gatherFrames.start()

    time.sleep(0.5)
    studentLocations, frameCount = yolo2sec()
    print(studentLocations)

    for l in studentLocations:
        utils.sendLocationsToDB(Utilities, (studentLocations.index(l) + 1), classInstanceID, l[0], [1], l[2], l[3])

    processing = ProcessingStudent(studentLocations, sensitivity, classInstanceID)
    frameCount = frameCount + frameRate

    while(True):
        check = feedEnd is True and frameCount == len(allImages)
        if check is True:
            break

        if(frameCount % frameRate == 0):
            # processing.runThreading(allImages[frameCount - frameRate: frameCount])
            processing.runSequential(allImages[frameCount - frameRate: frameCount])
        frameCount = frameCount + 1

    gatherFrames.join()

