import multiprocessing, json
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory, \
                               WebSocketServerProtocol, \
                               listenWS

class FaceServerProtocol(WebSocketServerProtocol):
    def __init__(self):
        super(FaceServerProtocol, self).__init__()
        self.training = False
        self.new_person = None
        #face_reg.recog_engine_init(serverip='120.27.21.223')
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
        print msg['type']
        if msg['type'] == "CONNECT_REQ":
            self.sendJsonMessage("CONNECT_RESP")
        elif msg['type'] == "LOADNAME_REQ":
            self.sendJsonMessage("LOADNAME_RESP", ",".join(self.peoples))
        elif msg['type'] == "DELETENAME_REQ":
            name = msg['msg'].encode('ascii', 'ignore')
            self.deleteName(name)
        elif msg['type'] == "TRAINSTART_REQ":
            name = msg['msg'].encode('ascii', 'ignore')
            if self.training == True:
                self.sendJsonMessage("ERROR_MSG","Already in training.")
            else:
                self.training = True
                self.sendJsonMessage("TRAINSTART_RESP")
            #self.new_person = face_reg.training_start(name)
            #print self.new_person
        elif msg['type'] == "TRAINFINISH_REQ":
            if self.training == False:
                self.sendJsonMessage("ERROR_MSG","Not in training.")
            else:
                self.onTrainFinish(None, None)
            #face_reg.training_finish(self.new_person, self.onTrainFinish)

    def onTrainFinish(self, name, feature):
        self.training = False
        self.new_person = None
        self.sendJsonMessage("LOADNAME_RESP", ",".join(self.peoples))
        self.sendJsonMessage("TRAINFINISH_RESP")

    def sendJsonMessage(self, mtype, msg = " "):
        msg = { "type" : mtype, 'msg' : msg }
        print(json.dumps(msg))
        self.sendMessage(json.dumps(msg))

    def deleteName(self, name)

    def recogThread(self):
        while (1):
            inFrame = self.img_queue.get()

            if self.training:
                rets = face_reg.training_proframe(self.new_person, inFrame)
            else:
                rets = face_reg.recog_process_frame(inFrame)

            self.res_queue.put(rets)

def socketServerProcess():
    factory = WebSocketServerFactory("ws://localhost:9000")
    factory.protocol = FaceServerProtocol
    listenWS(factory)
    reactor.run()

def startWebSocketServer():
    p = multiprocessing.Process(target = socketServerProcess)
    p.start()

