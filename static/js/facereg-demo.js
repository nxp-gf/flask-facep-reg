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


function btnStartOnclick(){
    var name = $("#addPersonTxt").val();
    if(document.getElementById("addPersonTxt").value=='')
    { alert("Please input your name!"); return; }

    console.log("in btnStartOnclick");
    sendMessage("TRAINSTART_REQ", name);
}

function btnFinishOnclick(){
    console.log("in btnFinishOnclick");
    sendMessage("TRAINFINISH_REQ", "");
}

function btnDeleteOnclick(){
    var name = $("#addPersonTxt").val();
    if(document.getElementById("addPersonTxt").value=='')
    { alert("Please input your name!"); return; }

    console.log("in btnDeleteOnclick");
    sendMessage("DELETENAME_REQ", name);
}

function redrawPeople(peopleNames) {
   document.getElementById("identity").value=peopleNames;
}

function sendMessage(type, msg) {
    var msg = {
               'type': type,
               'msg' : msg };
    socket.send(JSON.stringify(msg));
}

function createSocket(address) {
    socket = new WebSocket(address);
    socket.binaryType = "arraybuffer";
    socket.onopen = function() {
        console.log("On open");
        socket.send(JSON.stringify({'type': 'CONNECT_REQ'}));
        $("#serverStatus").html("Connected.");
        $("#trainingStatus").html("Recognizing.");
    }
    socket.onmessage = function(e) {
        console.log(e);
        j = JSON.parse(e.data)
        if (j.type == "CONNECT_RESP") {
            sendMessage("LOADNAME_REQ", "");
        } else if (j.type == "LOADNAME_RESP") {
            redrawPeople(j['msg']);
        } else if (j.type == "TRAINSTART_RESP") {
            $("#trainingStatus").html("Training.");
        } else if (j.type == "TRAINFINISH_RESP") {
            redrawPeople(j['msg']);
            $("#trainingStatus").html("Recognizing.");
        } else if (j.type == "ERROR_MSG") {
            alert(j['msg']);
        } else if (j.type == "TRAINPROCESS") {
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
