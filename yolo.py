import cv2
import time
import sys
import numpy as np
import os

Categories = ['Topwear', 'Bottomwear', 'Footwear', 'Eyewear', 'Handbag']

def build_model(is_cuda):
    net = cv2.dnn.readNet("config/best_25.onnx")
    if is_cuda:
        print("Attempty to use CUDA")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
    else:
        print("Running on CPU")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    return net

INPUT_WIDTH = 640
INPUT_HEIGHT = 640
SCORE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.4
CONFIDENCE_THRESHOLD = 0.4

def detect(image, net):
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (INPUT_WIDTH, INPUT_HEIGHT), swapRB=True, crop=False)
    net.setInput(blob)
    preds = net.forward()
    return preds

def load_capture():
    #capture = cv2.VideoCapture("sample.mp4")
    capture = cv2.imread('config/input.jpg')
    return capture

def load_classes():
    class_list = []
    with open("config/classes.txt", "r") as f:
        class_list = [cname.strip() for cname in f.readlines()]
    return class_list

class_list = load_classes()

def wrap_detection(input_image, output_data):
    class_ids = []
    confidences = []
    boxes = []

    rows = output_data.shape[0]

    image_width, image_height, _ = input_image.shape

    x_factor = image_width / INPUT_WIDTH
    y_factor =  image_height / INPUT_HEIGHT

    for r in range(rows):
        row = output_data[r]
        confidence = row[4]
        if confidence >= 0.4:

            classes_scores = row[5:]
            _, _, _, max_indx = cv2.minMaxLoc(classes_scores)
            class_id = max_indx[1]
            if (classes_scores[class_id] > .25):

                confidences.append(confidence)

                class_ids.append(class_id)

                x, y, w, h = row[0].item(), row[1].item(), row[2].item(), row[3].item() 
                left = int((x - 0.5 * w) * x_factor)
                top = int((y - 0.5 * h) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)
                box = np.array([left, top, width, height])
                boxes.append(box)

    #print(len(boxes))
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.25, 0.45) 
    #print(indexes)

    result_class_ids = []
    result_confidences = []
    result_boxes = []

    for i in indexes:
        result_confidences.append(confidences[i])
        result_class_ids.append(class_ids[i])
        result_boxes.append(boxes[i])

    return result_class_ids, result_confidences, result_boxes

def format_yolov5(frame):

    row, col, _ = frame.shape
    _max = max(col, row)
    result = np.zeros((_max, _max, 3), np.uint8)
    result[0:row, 0:col] = frame
    return result


colors = [(255, 255, 0), (0, 255, 0), (0, 255, 255), (255, 0, 0)]

is_cuda = len(sys.argv) > 1 and sys.argv[1] == "cuda"

net = build_model(is_cuda)
#capture = load_capture()

start = time.time_ns()
frame_count = 0
total_frames = 0
fps = -1

#while True:

#_, frame = capture.read()
frame = cv2.imread('temp/input.jpg')
#frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#frame = np.expand_dims(frame, axis=0) 
#frame = cv2.normalize(frame,None,0,1,cv2.NORM_MINMAX,dtype=cv2.CV_32F)
if frame is None:
    print("End of stream")
    exit()


def driver(img_path) :

    frame = cv2.imread(img_path)

    if frame is not None :


        inputImage = format_yolov5(frame)
        outs = detect(inputImage, net)
        class_ids, confidences, boxes = wrap_detection(inputImage, outs[0])
        #print(boxes)
        #print(class_ids)
        #print(confidences)

        #frame_count += 1
        #total_frames += 1
        for (classid, confidence, box) in zip(class_ids, confidences, boxes):
             color = colors[int(classid) % len(colors)]
             cv2.rectangle(frame, box, color, 2)
             cv2.rectangle(frame, (box[0], box[1] - 20), (box[0] + box[2], box[1]), color, -1)
             cv2.putText(frame, class_list[classid], (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,0,0))

        cv2.imwrite('temp/yolo_output.jpg', frame)

        '''if frame_count >= 30:
            end = time.time_ns()
            fps = 1000000000 * frame_count / (end - start)
            frame_count = 0
            start = time.time_ns()'''

        '''if fps > 0:
            fps_label = "FPS: %.2f" % fps
            cv2.putText(frame, fps_label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)'''
        #raw_img = cv2.imread('config/sample5.jpg')
        raw_img = cv2.imread('temp/input.jpg')

        print(boxes)
        #print()

        for index in range(len(boxes)) :
            box = boxes[index]
            #category = class_ids[index]
            category = Categories[class_ids[index]]

            cropped_img = raw_img[box[1] : box[1] + box[3], box[0] : box[0] + box[2]]
            cv2.imwrite(os.path.join('user_products', category) + '.jpg', cropped_img)
            #break
            #cv2.imshow("cropped", raw_img[box[1] : box[1] + box[3], box[0] : box[0] + box[2]])

        #print(box[0], box[0] + box[2], box[1], box[1] + box[3])
        #cropped_img = frame[130 : 320, 639 : 705]
        #cv2.imshow("output", frame)

        #cv2.imshow("cropped", cropped_img)
        '''if cv2.waitKey(0) > -1:
            print("finished by user")
            exit()

        print("Total frames: " + str(total_frames))'''