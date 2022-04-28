import json
import os
import subprocess
import threading
import time
from typing import List

import uvicorn
from fastapi import FastAPI, WebSocketDisconnect, WebSocket


def worker2(var):
    print(var)
    sudoPassword = "asi@123"
    os.system("echo %s | sudo docker restart koala_gateway_security_1" % (sudoPassword))
    os.system("echo %s | sudo docker restart koala_gateway_face_1" % (sudoPassword))
    time.sleep(10)


def worker3(status):
    sudoPassword = "asi@123"
    os.system("echo %s | sudo docker %s koala_gateway_security_1" % (sudoPassword, status))
    time.sleep(10)


def worker4(status):
    sudoPassword = "asi@123"
    os.system("echo %s | sudo docker %s koala_gateway_face_1" % (sudoPassword, status))
    time.sleep(10)


def worker1(media_name, time_sleep=5, status=0, serie='', pid=2):
    print(media_name)
    sudoPassword = "asi@123"
    if int(status) == 1:
        print("door opened")
        os.system("echo %s | sudo -S usbrelay %s_%s=1" % (sudoPassword, serie, pid))
        time.sleep(time_sleep)
        print("door closed")
        os.system("echo %s | sudo -S usbrelay %s_%s=0" % (sudoPassword, serie, pid))
    elif int(status) == 0:
        os.system("echo %s | sudo -S usbrelay %s_%s=1" % (sudoPassword, serie, pid))
        time.sleep(time_sleep)
        os.system("echo %s | sudo -S usbrelay %s_%s=0" % (sudoPassword, serie, pid))
    else:
        time.sleep(time_sleep)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


def worker0(_type, pid=2):
    sudoPassword = "asi@123"
    os.system("echo %s | sudo -S usbrelay _%s=%s" % (sudoPassword, pid, _type))


app = FastAPI()
manager = ConnectionManager()


@app.get("/")
async def root():
    return {"message": ":D"}


@app.get("/list/relay")
async def say_hello():
    cmd = "echo 1 | sudo -S usbrelay"
    a = subprocess.getoutput(cmd).split(' ')[-1]
    relays = a.split("\n")
    keys = []
    result = []
    for relay in relays:
        record = {}
        name = relay.split("_")[0]
        port = relay.split("_")[1]
        s_port = port.split("=")[0]
        if name not in keys:
            keys.append(name)
            record[name] = {"series": name, "num_port": 1, "status": {"1": "door"}}
            result.append(record.copy())
        else:
            for k in range(len(keys)):
                if list(result[k].keys())[0] == name:
                    result[k][name]['num_port'] += 1
                    result[k][name]['status'][s_port] = "secure"
    return result


@app.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            print(data["type"])
            if data["type"] == "secure":
                p1 = threading.Thread(target=worker1, args=(
                    "warning.mp3", data["time_alarm"], 0, data["relay_name"], data["relay_port"],))
                p1.start()
            elif data["type"] == "face":
                print(data["subject_type"])
                if int(data["subject_type"]) == 0:
                    p1 = threading.Thread(target=worker1, args=(
                        "staff.mp3", data["time_open"], 1, data["relay_name"], data["relay_port"],))
                    p1.start()
                    break
                elif int(data["subject_type"]) == 1:
                    p1 = threading.Thread(target=worker1, args=(
                        "visit.mp3", data["time_open"], 1, data["relay_name"], data["relay_port"],))
                    p1.start()
                    break
                elif int(data["subject_type"]) == 3:
                    p1 = threading.Thread(target=worker1, args=(
                        "warning.mp3", data["time_open"], 0, data["relay_name"], data["relay_port"],))
                    p1.start()
                    break
                else:
                    p1 = threading.Thread(target=worker1,
                                          args=("stranger.mp3", 2, 2, data["relay_name"], data["relay_port"],))
                    p1.start()
                    break
            elif data["type"] == "door":
                p1 = threading.Thread(target=worker1, args=("door.mp3", 5, 1, data["relay_port"],))
                p1.start()
            elif data['type'] == "restart":
                p1 = threading.Thread(target=worker2, args=("restart",))
                p1.start()
            elif data["type"] == "stop_secure":
                cmd = ["docker", "inspect", "-f", "'{{.State.Status}}'", "koala_gateway_security_1"]
                if subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode() == "running":
                    p1 = threading.Thread(target=worker3, args=("stop",))
                    p1.start()
            elif data["type"] == "start_secure":
                cmd = ["docker", "inspect", "-f", "'{{.State.Status}}'", "koala_gateway_security_1"]
                if subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode() != "running":
                    p1 = threading.Thread(target=worker3, args=("start",))
                    p1.start()
            elif data["type"] == "stop_face":
                cmd = ["docker", "inspect", "-f", "'{{.State.Status}}'", "koala_gateway_face_1"]
                if subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode() == "running":
                    p1 = threading.Thread(target=worker4, args=("stop",))
                    p1.start()
            elif data["type"] == "start_face":
                cmd = ["docker", "inspect", "-f", "'{{.State.Status}}'", "koala_gateway_face_1"]
                if subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode() != "running":
                    p1 = threading.Thread(target=worker4, args=("start",))
                    p1.start()
            elif data["type"] == "turn_off":
                p1 = threading.Thread(target=worker0, args=("0", data["relay_port"],))
                p1.start()
            elif data["type"] == "turn_on":
                p1 = threading.Thread(target=worker0, args=("1", data["relay_port"],))
                p1.start()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client left the chat")


if __name__ == "__main__":
    uvicorn.run("wbs:app", host="0.0.0.0", port=5679, reload=True)
