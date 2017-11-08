/*
Copyright 2015-2016 Carnegie Mellon University

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

window.URL = window.URL ||
    window.webkitURL ||
    window.msURL ||
    window.mozURL;

function trainingChkCallback() {
    console.log("in trainingChkCallback");
    training = $("#trainingChk").prop('checked');


    if (training) {
        var newPerson = $("#addPersonTxt").val();

        if(document.getElementById("addPersonTxt").value=='')
        { alert("Please input your name!"); return; }

        if (socket != null) {
            var msg = {
                'type': 'TRAINING_START',
                'val': newPerson
            };
            socket.send(JSON.stringify(msg));
        }
    } else {
        if (socket != null) {
            var msg = {
                'type': 'TRAINING_FINISH',
                'val': ""
            };
            socket.send(JSON.stringify(msg));
        }
    }
}


function redrawPeople() {
   document.getElementById("identity").value=people;
}

function sendIndentityReq() {
    var msg = {
        'type': 'IDENTITY_REQ',
        'training': training
    };
    socket.send(JSON.stringify(msg));
}

function createSocket(address, name) {
    socket = new WebSocket(address);
    socketName = name;
    socket.binaryType = "arraybuffer";
    socket.onopen = function() {
        $("#serverStatus").html("Connected to " + name);
        sentTimes = [];
        receivedTimes = [];
        tok = defaultTok;
        numNulls = 0

        socket.send(JSON.stringify({'type': 'NULL'}));
        sentTimes.push(new Date());
    }
    socket.onmessage = function(e) {
//        console.log(e);
        j = JSON.parse(e.data)
        if (j.type == "NULL") {
            receivedTimes.push(new Date());
            numNulls++;
            if (numNulls == defaultNumNulls) {
                sendIndentityReq();
            } else {
                socket.send(JSON.stringify({'type': 'NULL'}));
                sentTimes.push(new Date());
            }
        } else if (j.type == "PROCESSED") {
            tok++;
        } else if (j.type == "IDENTITY_RESP") {
            people = j['content'];
            redrawPeople();
        } else if (j.type == "ANNOTATED") {
        } else if (j.type == "TSNE_DATA") {
        } else {
            console.log("Unrecognized message type: " + j.type);
        }
    }
    socket.onerror = function(e) {
        console.log("Error creating WebSocket connection to " + address);
        console.log(e);
    }
    socket.onclose = function(e) {
        if (e.target == socket) {
            $("#serverStatus").html("Disconnected.");
        }
    }
}

function umSuccess(stream) {
    console.log("in umSuccess");
    if (vid.mozCaptureStream) {
        vid.mozSrcObject = stream;
    } else {
        vid.src = (window.URL && window.URL.createObjectURL(stream)) ||
            stream;
    }
    vid.play();
    vidReady = true;
}

function changeServerCallback() {
    $(this).addClass("active").siblings().removeClass("active");
    switch ($(this).html()) {
    case "Local":
        socket.close();
        createSocket("wss:" + window.location.hostname + ":9000", "Local");
        break;
    case "CMU":
        socket.close();
        createSocket("wss://facerec.cmusatyalab.org:9000", "CMU");
        break;
    case "AWS East":
        socket.close();
        createSocket("wss://54.159.128.49:9000", "AWS-East");
        break;
    case "AWS West":
        socket.close();
        createSocket("wss://54.188.234.61:9000", "AWS-West");
        break;
    default:
        alert("Unrecognized server: " + $(this.html()));
    }
}
