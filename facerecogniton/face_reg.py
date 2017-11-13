'''
Main program
@Author: David Vu

To execute simply run:
main.py

To input new user:
main.py --mode "input"

'''

import cv2
from align_custom import AlignCustom
from face_feature import FaceFeature
from mtcnn_detect import MTCNNDetect
from tf_graph import FaceRecGraph
import argparse
import sys, time
import json
import numpy as np
from PIL import Image
import StringIO


FRGraph = FaceRecGraph();
aligner = AlignCustom();
extract_feature = FaceFeature(FRGraph)
face_detect = MTCNNDetect(FRGraph, scale_factor=2); #scale_factor, rescales image for faster detection
feature_data_set = None


def main(args):
    mode = args.mode
    if(mode == "camera"):
        camera_recog()
    elif mode == "input":
        create_manual_data();
    else:
        raise ValueError("Unimplemented mode")
'''
Description:
Images from Video Capture -> detect faces' regions -> crop those faces and align them 
    -> each cropped face is categorized in 3 types: Center, Left, Right 
    -> Extract 128D vectors( face features)
    -> Search for matching subjects in the dataset based on the types of face positions. 
    -> The preexisitng face 128D vector with the shortest distance to the 128D vector of the face on screen is most likely a match
    (Distance threshold is 0.6, percentage threshold is 70%)
    
'''


tracker = None
def track_people(frame, bbox):
    global tracker
    # Set up tracker.
    # Instead of MIL, you can also use
 
    tracker_types = ['BOOSTING', 'MIL','KCF', 'TLD', 'MEDIANFLOW', 'GOTURN']
    tracker_type = tracker_types[2]
 
    if 1 < 3:
        tracker = cv2.Tracker_create(tracker_type)
    else:
        if tracker_type == 'BOOSTING':
            tracker = cv2.TrackerBoosting_create()
        if tracker_type == 'MIL':
            tracker = cv2.TrackerMIL_create()
        if tracker_type == 'KCF':
            tracker = cv2.TrackerKCF_create()
        if tracker_type == 'TLD':
            tracker = cv2.TrackerTLD_create()
        if tracker_type == 'MEDIANFLOW':
            tracker = cv2.TrackerMedianFlow_create()
        if tracker_type == 'GOTURN':
            tracker = cv2.TrackerGOTURN_create()
 
    # Define an initial bounding box
    bbox = (287, 23, 86, 320)
 
    # Uncomment the line below to select a different bounding box
    bbox = cv2.selectROI(frame, False)
 
    # Initialize tracker with first frame and bounding box
    ok = tracker.init(frame, bbox)
 
def recog_process_frame_with_tracker(frame):
    global tracker
    #print "111  ", int(round(time.time() * 1000))
    #u can certainly add a roi here but for the sake of a demo i'll just leave it as simple as this
    rects, landmarks = face_detect.detect_face(frame,10);#min face size is set to 80x80
    for (i,rect) in enumerate(rects):
        cv2.rectangle(frame,(rect[0],rect[1]),(rect[0] + rect[2],rect[1]+rect[3]),(0,0,255),2)
        if (tracker is None):
            track_people(frame,rect)
        else:
            # Start timer
            timer = cv2.getTickCount()
 
            # Update tracker
            ok, bbox = tracker.update(frame)
 
            # Draw bounding box
            if ok:
                # Tracking success
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)
            else :
                # Tracking failure
                cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
 
    return rects

def detect_people(frame):
    rets = []
    rects, landmarks = face_detect.detect_face(frame,80);#min face size is set to 80x80
    for (i,rect) in enumerate(rects):
        rets.append({"name":"  ", "pos":rect})

    return rets

def recog_process_frame(frame):
#    print("11111111111112312311")
    rects, landmarks = face_detect.detect_face(frame,40);#min face size is set to 80x80
    aligns = []
    positions = []
    rets = []
#    print("11111111111111")
    for (i, rect) in enumerate(rects):
        aligned_face, face_pos = aligner.align(160,frame,landmarks[i])
        aligns.append(aligned_face)
        positions.append(face_pos)
#    print("1111111112222222211111")
    if (len(aligns) == 0):
        return rets
    features_arr = extract_feature.get_features(aligns)
    recog_data = findPeople(features_arr,positions);
#    print("111111111333333332222222211111")
    for (i,rect) in enumerate(rects):
        rets.append({"name":recog_data[i], "pos":rect})
#        cv2.rectangle(frame,(rect[0],rect[1]),(rect[0] + rect[2],rect[1]+rect[3]),(0,0,255),2) #draw bounding box for the face
#        cv2.putText(frame, recog_data[i],(rect[0],rect[1]),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
    return rets

'''
facerec_128D.txt Data Structure:
{
"Person ID": {
    "Center": [[128D vector]],
    "Left": [[128D vector]],
    "Right": [[128D Vector]]
    }
}
This function basically does a simple linear search for 
^the 128D vector with the min distance to the 128D vector of the face on screen
'''
def findPeople(features_arr, positions, thres = 0.5, percent_thres = 90):
    '''
    :param features_arr: a list of 128d Features of all faces on screen
    :param positions: a list of face position types of all faces on screen
    :param thres: distance threshold
    :return: person name and percentage
    '''
    regRes = [];
    for (i,features_128D) in enumerate(features_arr):
        returnRes = "Unknown";
        smallest = sys.maxsize
        for person in feature_data_set.keys():
            person_data = feature_data_set[person][positions[i]];
            for data in person_data:
                distance = np.sqrt(np.sum(np.square(data-features_128D)))
                if(distance < smallest):
                    smallest = distance;
                    returnRes = person;
        percentage =  min(100, 100 * thres / smallest)
        if percentage <= percent_thres :
            regRes.append("Unknown")
        else:
            regRes.append(returnRes+"-"+str(round(percentage,1))+"%")
    return regRes

'''
Description:
User input his/her name or ID -> Images from Video Capture -> detect the face -> crop the face and align it 
    -> face is then categorized in 3 types: Center, Left, Right 
    -> Extract 128D vectors( face features)
    -> Append each newly extracted face 128D vector to its corresponding position type (Center, Left, Right)
    -> Press Q to stop capturing
    -> Find the center ( the mean) of those 128D vectors in each category. ( np.mean(...) )
    -> Save
    
'''
class PersonModel:
    def __init__(self, name):
        self.name = name
        self.person_imgs = {"Left" : [], "Right": [], "Center": []};
        self.feature = None
        self.images = []

def training_start_local(name):
    if(has_name(name)):
        return None
    return PersonModel(name)

def training_proframe_local(model, frame):
    rects, landmarks = face_detect.detect_face(frame, 80);  # min face size is set to 80x80
    for (i, rect) in enumerate(rects):
        aligned_frame, pos = aligner.align(160,frame,landmarks[i]);
        model.person_imgs[pos].append(aligned_frame)
    for (i,rect) in enumerate(rects):
        cv2.rectangle(frame,(rect[0],rect[1]),(rect[0] + rect[2],rect[1]+rect[3]),(255,0,0))
    return frame

def __training_thread_local(model, callback):
    person_features = {"Left" : [], "Right": [], "Center": []};
    for pos in model.person_imgs:
        person_features[pos] = [np.mean(extract_feature.get_features(
                                         model.person_imgs[pos]),axis=0).tolist()]
    if (feature_data_set is not None):
        __save_person_features(model.name, person_features)
    callback(model.name, person_features)

def training_finish_local(model, callback):
    t = threading.Thread(target=__training_thread_local, args=(model, callback,))
    t.start()
    return t

def __save_person_features(name, features):
    feature_data_set[name] = features;
    f = open('./models/facerec_128D.txt', 'w');
    f.write(json.dumps(feature_data_set))

def get_person_names():
    names = []
    for name in feature_data_set:
        names.append(name)
    return names

def has_name(name):
    return feature_data_set.has_key(name)

def delete_person_name(name):
    if (has_name(name)):
        del feature_data_set[name];
        f = open('./models/facerec_128D.txt', 'w');
        f.write(json.dumps(feature_data_set))

import requests
import threading

url = 'http://10.193.20.74:8383/train'

def __training_thread_remote(model, callback):
    args = {'id': model.name, 'end':'true'}
    headers = {"Content-type":"application/json","Accept": "application/json"}
    files = {}
    for i,f in enumerate(model.images):
        files['file{}'.format(i)] = ('{}.png'.format(i), f, 'image/png')
#    files = {'file': ('pic.png', picf, 'image/png')}
    r = requests.post(url, params=args, files=files)
#    r = requests.post(url, params=args)

    args = {'id': model.name}
    headers = {"Content-type":"application/json","Accept": "application/json"}
    while (True):
        time.sleep(1)
        r = requests.get(url, params=args, headers=headers)
        ret = json.loads(r.text)
        if ('state'in ret and ret['state'] == 'FINISH'):
            __save_person_features(model.name, ret['feature'])
            callback(model.name, r.text)
            headers = {"Content-type":"application/json","Accept": "application/json"}
            r = requests.delete(url, params=args, headers=headers)
            break

def training_start_remote(name):
    args = {'id': name}
    headers = {"Content-type":"application/json","Accept": "application/json"}
    r = requests.put(url, params=args, headers=headers)
    return PersonModel(name)

def training_proframe_remote(model, frame):
    picf = StringIO.StringIO()
    pi = Image.fromarray(frame)
    pi.save(picf, format = "jpeg")
    picf.seek(0)

    model.images.append(picf)
#    args = {'id': model.name, 'end':'false'}
#    files = {'file': ('pic.png', picf, 'image/png')}
#    r = requests.post(url, params=args, files=files)

def training_finish_remote(model, callback):
    t = threading.Thread(target=__training_thread_remote, args=(model, callback,))
    t.start()
    return t

training_start = training_start_local
training_proframe = training_proframe_local
training_finish = training_finish_local

def recog_engine_init(serverip=None):
    global training_start, training_proframe, training_finish
    if (serverip is not None):
        global url
        url = 'http://{}:8383/train'.format(serverip)
        training_start = training_start_remote
        training_proframe = training_proframe_remote
        training_finish = training_finish_remote
    global feature_data_set
    f = open('./models/facerec_128D.txt','r');
    feature_data_set = json.loads(f.read());


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, help="Run camera recognition", default="camera")
    args = parser.parse_args(sys.argv[1:])
    main(args);
