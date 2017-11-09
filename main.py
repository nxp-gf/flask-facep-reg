#!/usr/bin/env python
from importlib import import_module
import os,time
from flask import Flask, render_template, Response
from websocket import startWebSocketServer 

from camera_opencv import *

app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        time.sleep(0.050)
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/videoel')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    startWebSocketServer()
    app.run(host='0.0.0.0', threaded=True)

