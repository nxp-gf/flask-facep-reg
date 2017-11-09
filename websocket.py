import json
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory, \
                               WebSocketServerProtocol, \
                               listenWS

from multiprocessing import Process, Queue, Lock
from camera_opencv import  frame_queue, retsult_queue
import threading, time

toRecogQueue = Queue(maxsize = 1)
fromRecogQueue = Queue(maxsize = 1)

def recogProcess():
    import facerecogniton.face_reg as face_reg
    face_reg.recog_engine_init(serverip='10.193.20.77')

    recogProcess.training = False
    recogProcess.new_person = None
    def sendQueueMessage(mtype, msg=""):
        msg = { "type" : mtype, 'msg' : msg }
        print("In recog thread send:", json.dumps(msg))
        fromRecogQueue.put(msg)

    def onTrainFinish(name, feature):
        recogProcess.training = False
        recogProcess.new_person = None
        peoples = face_reg.get_person_names()
        sendQueueMessage("TRAINFINISH_RESP", peoples)

    def msgProcessThread():
        print("msgProcessThread start")
        while (1):
            try:
                msg = toRecogQueue.get()
                if msg['type'] == "LOADNAME_REQ":
                    peoples = face_reg.get_person_names()
                    sendQueueMessage("LOADNAME_RESP", peoples)
                elif msg['type'] == "DELETENAME_REQ":
                    face_reg.delete_person_name(msg['msg'])
                    peoples = face_reg.get_person_names()
                    sendQueueMessage("LOADNAME_RESP", peoples)
                elif msg['type'] == "TRAINSTART_REQ":
                    if recogProcess.training == True:
                        sendQueueMessage("ERROR_MSG","Already in training.")
                    else:
                        recogProcess.training = True
                        recogProcess.new_person = face_reg.training_start(msg['msg'])
                        sendQueueMessage("TRAINSTART_RESP")
                elif msg['type'] == "TRAINFINISH_REQ":
                    if recogProcess.training == False:
                        sendQueueMessage("ERROR_MSG","Not in training.")
                    else:
                        face_reg.training_finish(recogProcess.new_person, onTrainFinish)
                        sendQueueMessage("TRAINPROCESS")

            except Exception,e:
               print e
    print("recogProcess start")
    t1 = threading.Thread(target=msgProcessThread)
    t1.start()
#    while (1):
#        pass
    while (1):
        try:
            inFrame = frame_queue.get()

            if recogProcess.training:
                face_reg.training_proframe(recogProcess.new_person, inFrame)
            else:
                rets = face_reg.recog_process_frame(inFrame)
                retsult_queue.put(rets)
        except Exception,e:  
            print e  

class FaceServerProtocol(WebSocketServerProtocol):
    def __init__(self):
        super(FaceServerProtocol, self).__init__()
        self.new_person = None
        self.peoples = []
        reactor.callLater(1,self.timerCallback)

    def timerCallback(self):
        try:
            ret = fromRecogQueue.get_nowait()
            print("get msg from recog", json.dumps(ret))
            if (ret["type"] == "TRAINFINISH_RESP"):
                self.peoples = ret['msg']
            self.sendSocketMessage(ret["type"], ret["msg"])
        except Exception,e:
           print e
        reactor.callLater(1,self.timerCallback)

    def onOpen(self):
        print "open"

    def onClose(self, wasClean, code, reason):
        print "close"

    def onMessage(self, payload, binary):
        raw = payload.decode('utf8')
        msg = json.loads(raw)
        if msg['type'] == "CONNECT_REQ":
            self.sendSocketMessage("CONNECT_RESP")
        elif msg['type'] == "LOADNAME_REQ":
            ret = self.sendQueueMessage("LOADNAME_REQ")
            self.peoples = ret['msg']
            self.sendSocketMessage(ret["type"], ret["msg"])
        elif msg['type'] == "DELETENAME_REQ":
            name = msg['msg'].encode('ascii', 'ignore')
            if (name in self.peoples):
                ret = self.sendQueueMessage("DELETENAME_REQ", name)
                self.peoples = ret['msg']
                self.sendSocketMessage(ret["type"], ret["msg"])
            else:
                self.sendSocketMessage("ERROR_MSG", name + " is not in database")
        elif msg['type'] == "TRAINSTART_REQ":
            name = msg['msg'].encode('ascii', 'ignore')
            if (name in self.peoples):
                self.sendSocketMessage("ERROR_MSG", name + " is already in database")
            else:
                ret = self.sendQueueMessage("TRAINSTART_REQ", name)
                self.sendSocketMessage(ret["type"], ret["msg"])
        elif msg['type'] == "TRAINFINISH_REQ":
            ret = self.sendQueueMessage("TRAINFINISH_REQ")
            self.sendSocketMessage(ret["type"], ret["msg"])

    def onTrainFinish(self, name, feature):
        self.peoples = face_reg.get_person_names()
        self.sendSocketMessage("LOADNAME_RESP", ",".join(self.peoples))
        self.sendSocketMessage("TRAINFINISH_RESP")

    def sendSocketMessage(self, mtype, msg = ""):
        msg = { "type" : mtype, 'msg' : msg }
        print("send sendSocketMessage:",json.dumps(msg))
        self.sendMessage(json.dumps(msg))

    def sendQueueMessage(self, mtype, msg=""):
        msg = { "type" : mtype, 'msg' : msg }
        print("send sendQueueMessage:",json.dumps(msg))
        toRecogQueue.put(msg)
        ret = fromRecogQueue.get()
        print("get msg from recog", json.dumps(ret))
        return ret


def socketServerProcess():
    factory = WebSocketServerFactory("ws://localhost:9000")
    factory.protocol = FaceServerProtocol
    listenWS(factory)
    reactor.run()

def startWebSocketServer():
    p1 = Process(target = recogProcess)
    p1.start()
    time.sleep(100)
    print("Sleep out")
    p2 = Process(target = socketServerProcess)
    p2.start()

