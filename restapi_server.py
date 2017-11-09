#!/usr/bin/env python
# -*- coding: utf-8 -*-
# by vellhe 2017/7/9
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource, request
import werkzeug
import os
import StringIO


import facerecogniton.face_reg as face_reg

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('id', type=str, location='args')
parser.add_argument('end', type=str, location='args')
parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')


def remove_dir(dir):
    if(os.path.isdir(dir)):
        for p in os.listdir(dir):
            remove_dir(os.path.join(dir,p))
        if(os.path.exists(dir)):
            os.rmdir(dir)
    else:
        if(os.path.exists(dir)):
            os.remove(dir)

class TrainModels(Resource):
    modles = {}
    def __add_modle(self, name):
        if name not in self.modles:
            self.modles[name] = {'state':'INIT', 'features':None, 'count':0}

    def __del_modle(self, name):
        if name in self.modles:
            del self.modles[name]

    def __get_modle_features(self, name):
        if name not in self.modles:
            ret = {'state':'NONAME'}
        elif self.modles[name]['features'] is None:
            ret = {'state':'TRAINING'}
        else:
            ret = {'state':'FINISH', 'feature':self.modles[name]['features']}
        return ret

    def __train_modle(self, name, images):
        if name not in self.modles or len(images) == 0:
            return
        pmodel = face_reg.training_start(name)
        for picf in images:
            face_reg.training_proframe(pmodel, picf)
        face_reg.training_finish(pmodel, self.__train_finish)

    def __train_finish(self, name, features):
        print '__train_finish'
        if name in self.modles:
            self.modles[name]['features'] = features

    def get(self):
        args = parser.parse_args()
        ret = self.__get_modle_features(args['id'])
        return ret, 200

    def delete(self):
        args = parser.parse_args()
        self.__del_modle(args['id'])
        return 'SUCCESS', 200

    def put(self):
        args = parser.parse_args()
        self.__add_modle(args['id'])
        return 'SUCCESS', 201

    def post(self):
        args = parser.parse_args()
        images = []
        for fname, f in request.files.items():
            pif=StringIO.StringIO()
            f.save(pif)
            images.append(pif)
        self.__train_modle(args['id'], images)
        return 'SUCCESS', 201

##
## Actually setup the Api resource routing here
##
api.add_resource(TrainModels, '/train')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8383, debug=True)
