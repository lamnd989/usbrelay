import asyncio
import json
import os
import threading
import time

import vlc
import websockets


def worker2():
    sudoPassword = "asi@123"
    os.system("echo %s | sudo docker restart koala_gateway_1" % (sudoPassword))

def worker1(media_name, time_sleep=5, status=0, pid=2):
    sudoPassword = "asi@123"
    p = vlc.MediaPlayer(media_name)
    p.play()
    if int(status) == 1:
        print("door opened")
        os.system("echo %s | sudo -S usbrelay _%s=1" % (sudoPassword, pid))
        time.sleep(time_sleep)
        print("door closed")
        os.system("echo %s | sudo -S usbrelay _%s=0" % (sudoPassword, pid))
    elif int(status) == 0:
        os.system("echo %s | sudo -S usbrelay _%s=1" % (sudoPassword, pid))
        time.sleep(time_sleep)
        os.system("echo %s | sudo -S usbrelay _%s=0" % (sudoPassword, pid))
    else:
        time.sleep(time_sleep)
    p.stop()


async def servers(websocket, path):
    async for name in websocket:
        data = json.loads(name)
        print(data["type"])
        if data["type"] == "secure":
            p1 = threading.Thread(target=worker1, args=("warning.mp3", 10, 0, 2))
            p1.start()
        elif data["type"] == "face":
            print(data["subject_type"])
            if int(data["subject_type"]) == 0:
                p1 = threading.Thread(target=worker1, args=("staff.mp3", 5, 1, 1))
                p1.start()
                break
            elif int(data["subject_type"]) == 1:
                p1 = threading.Thread(target=worker1, args=("visit.mp3", 5, 1, 1))
                p1.start()
                break
            elif int(data["subject_type"]) == 3:
                p1 = threading.Thread(target=worker1, args=("warning.mp3", 3, 0, 2))
                p1.start()
                break
            else:
                p1 = threading.Thread(target=worker1, args=("stranger.mp3", 2, 2, 1))
                p1.start()
                break
        elif data["type"] == "door":
            p1 = threading.Thread(target=worker1, args=("door.mp3", 5, 1, 1))
            p1.start()
        else:
            p1 = threading.Thread(target=worker2(), args=())
            p1.start()


if __name__ == "__main__":
    print("Started websocket server at port 5679!")
    start_server = websockets.serve(servers, "0.0.0.0", 5679)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
