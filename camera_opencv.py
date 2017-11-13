import cv2
from base_camera import BaseCamera
from imutils import paths


from multiprocessing import Queue
import facerecogniton.face_reg as face_reg
face_reg.recog_engine_init(serverip='10.193.20.77')


frame_queue = Queue(maxsize = 1)
retsult_queue = Queue(maxsize = 1)

def variance_of_laplacian(image):
   # compute the Laplacian of the image and then return the focus                                                                     
   # measure, which is simply the variance of the Laplacian
   return cv2.Laplacian(image, cv2.CV_64F).var()


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
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            #if retsult_queue.full():
            #    Camera.reg_ret = retsult_queue.get()
            
            # read current frame
            _, img = camera.read()
            rets = face_reg.detect_people(img)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            fm = variance_of_laplacian(gray)
            print(fm)
            for ret in rets:
                #draw bounding box for the face
                rect = ret['pos']
                cv2.rectangle(img,(rect[0],rect[1]),(rect[0] + rect[2],rect[1]+rect[3]),(0,0,255),2)
                cv2.putText(img, ret['name'],(rect[0],rect[1]),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
            if len(rets) == 0:
                print("Not get face")
            #try:
            #    if (frame_queue.full()):
            #        frame_queue.get_nowait()
            #    frame_queue.put(img)
            #except Exception as e:
            #    pass



            # encode as a jpeg image and return it
            yield cv2.imencode('.png', img)[1].tobytes()
