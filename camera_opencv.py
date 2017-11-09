import cv2
from base_camera import BaseCamera
#import facerecogniton.face_reg as face_reg
import threading, Queue


#face_reg.recog_engine_init(serverip='120.27.21.223')
#peoples = face_reg.get_person_names()
#print(peoples)

#img_queue = Queue.Queue(maxsize = 1)
#ret_queue = Queue.Queue(maxsize = 1)
#def recogThread():
#    while (1):
#        frame = img_queue.get()
#        ret = face_reg.recog_thread(frame)
#        if (ret is not None):
#            ret_queue.put(ret)

#p = threading.Thread(target=recogThread, args=())
#p.start()

def get_result():
    img = ret_queue.get()
    return cv2.imencode('.jpg', img)[1].tobytes()

class Camera(BaseCamera):
    video_source = 0

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def frames():
        camera = cv2.VideoCapture(Camera.video_source)
        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            _, img = camera.read()
            #rets = face_reg.detect_people(img)
            #if (img_queue.full()):
            #    img_queue.get_nowait()
            #img_queue.put(img)

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()
