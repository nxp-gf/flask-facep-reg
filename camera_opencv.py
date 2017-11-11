import cv2
from base_camera import BaseCamera

from multiprocessing import Queue


frame_queue = Queue(maxsize = 1)
retsult_queue = Queue(maxsize = 1)


class Camera(BaseCamera):
    video_source = 0
    reg_ret = []

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def frames():
        global frame_queue,regret_queue

        camera = cv2.VideoCapture(Camera.video_source)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            if retsult_queue.full():
                Camera.reg_ret = retsult_queue.get()
            
            # read current frame
            _, img = camera.read()
            for ret in Camera.reg_ret:
                #draw bounding box for the face
                rect = ret['pos']
                cv2.rectangle(img,(rect[0],rect[1]),(rect[0] + rect[2],rect[1]+rect[3]),(0,0,255),2)
                cv2.putText(img, ret['name'],(rect[0],rect[1]),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
            try:
                if (frame_queue.full()):
                    frame_queue.get_nowait()
                frame_queue.put(img)
            except Exception as e:
                pass



            # encode as a jpeg image and return it
            yield cv2.imencode('.jpeg', img)[1].tobytes()
