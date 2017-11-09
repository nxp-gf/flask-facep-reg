import json
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory, \
                               WebSocketServerProtocol, \
                               listenWS

from multiprocessing import Process, Queue
from camera_opencv import  frame_queue, retsult_queue

def recogProcess():
    import facerecogniton.face_reg as face_reg
    face_reg.recog_engine_init(serverip='120.27.21.223')
    while (1):
        try:
            inFrame = frame_queue.get()

            if FaceServerProtocol.training:
                face_reg.training_proframe(self.new_person, inFrame)
            else:
                rets = face_reg.recog_process_frame(inFrame)
                retsult_queue.put(rets)
        except Exception,e:  
            print e  

class FaceServerProtocol(WebSocketServerProtocol):
    training = False

    def __init__(self):
        super(FaceServerProtocol, self).__init__()
        self.new_person = None
        #face_reg.recog_engine_init(serverip='ec2-54-202-53-170.us-west-2.compute.amazonaws.com')
        #face_reg.recog_engine_init()
        #face_reg.recog_engine_init(serverip='47.95.202.40')
        #self.peoples = face_reg.get_person_names()
        self.peoples = ["gf", "wy"]

    def onOpen(self):
        print "open"

    def onClose(self, wasClean, code, reason):
        print "close"

    def onMessage(self, payload, binary):
        raw = payload.decode('utf8')
        msg = json.loads(raw)
        if msg['type'] == "CONNECT_REQ":
            self.sendJsonMessage("CONNECT_RESP")
        elif msg['type'] == "LOADNAME_REQ":
            self.sendJsonMessage("LOADNAME_RESP", ",".join(self.peoples))
        elif msg['type'] == "DELETENAME_REQ":
            name = msg['msg'].encode('ascii', 'ignore')
            self.deleteName(name)
        elif msg['type'] == "TRAINSTART_REQ":
            name = msg['msg'].encode('ascii', 'ignore')
            if FaceServerProtocol.training == True:
                self.sendJsonMessage("ERROR_MSG","Already in training.")
            elif (name in self.peoples):
                self.sendJsonMessage("ERROR_MSG", name + "is already in database")
            else:
                FaceServerProtocol.training = True
                self.sendJsonMessage("TRAINSTART_RESP")
                #self.new_person = face_reg.training_start(name)
            #print self.new_person
        elif msg['type'] == "TRAINFINISH_REQ":
            if FaceServerProtocol.training == False:
                self.sendJsonMessage("ERROR_MSG","Not in training.")
            else:
                self.onTrainFinish(None, None)
            #face_reg.training_finish(self.new_person, self.onTrainFinish)

    def onTrainFinish(self, name, feature):
        FaceServerProtocol.training = False
        self.new_person = None
        self.peoples = face_reg.get_person_names()
        self.sendJsonMessage("LOADNAME_RESP", ",".join(self.peoples))
        self.sendJsonMessage("TRAINFINISH_RESP")

    def sendJsonMessage(self, mtype, msg = " "):
        msg = { "type" : mtype, 'msg' : msg }
        print(json.dumps(msg))
        self.sendMessage(json.dumps(msg))

    def deleteName(self, name):
        if (name in self.peoples):
            face_reg.delete_person_name(name)
            self.sendJsonMessage("LOADNAME_RESP", ",".join(self.peoples))
        else:
            self.sendJsonMessage("ERROR_MSG", name + "is not in database")


def socketServerProcess():

    factory = WebSocketServerFactory("ws://localhost:9000")
    factory.protocol = FaceServerProtocol
    listenWS(factory)
    reactor.run()

def startWebSocketServer():
    p1 = Process(target = recogProcess)
    p1.start()
    p2 = Process(target = socketServerProcess)
    p2.start()

