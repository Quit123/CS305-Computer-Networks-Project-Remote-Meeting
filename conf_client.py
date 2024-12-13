import asyncio
import util
import time
from conf_opt import *
from util import *
from config import *
from flask import Flask, request, jsonify
import asyncio
from log_register_func import *
import api
import threading
from conf_server import ConferenceServer,MainServer

established_client = None


class ConferenceClient:
    def __init__(self, host='127.0.0.1'):
        # sync client
        self.host = host
        self.user_name = None
        self.log_status = False
        self.support_data_types = ['text', 'audio', 'camera']
        #self.support_data_types = ['screen', 'camera', 'audio', 'text']  # for some types of data
        self.acting_data_types = {data_type: False for data_type in ['screen', 'camera', 'audio']}
        self.acting_data_types['text'] = True  # 这里使用前端控制，delete
        self.acting_data_types['audio'] = True
        self.acting_data_types['camera'] = True
        self.ports = {'audio': 8001, 'screen': 8002, 'camera': 8003, 'text': 8004}
        # 初始化字典
        # 用来存不同类型的socket
        self.sockets = {}
        # you may need to save received streamd data from other clients in conference
        # 接受不同来源user的camera信息
        self.camera_queues = {}
        # self.data_queues = {
        #     'camera': asyncio.Queue(),
        # }
        self.text = None
        self.text_event = asyncio.Event()  # 用于通知 send_texts 有新数据
        self.loop = asyncio.get_event_loop()
        self.server_addr = (SERVER_IP, MAIN_SERVER_PORT)  # server addr
        self.conference_id = None
        self.is_working = True
        self.on_meeting = False  # status
        self.can_share_screen = True
        self.conference_info = None  # you may need to save and update some conference_info regularly
        self.create_event = asyncio.Event()
        self.quit_event = asyncio.Event()
        self.cancel_event = asyncio.Event()
        self.join_event = asyncio.Event()
        self.established_client = None

    async def create_conference(self, title_name):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        receive conference id.
        """
        print("[Info]: Creating a new conference...")
        request_data = f"[COMMAND]: Create Conference {title_name}"
        # 这里用来讲建立交流链接，text，和命令交流
        print("test1")
        response = await self.send_request(request_data)
        print("test2")
        print("response:", response)
        if "SUCCESS" in response:
            # 回复格式 SUCCESS 123456
            self.conference_id = response.split()[1]
            self.on_meeting = True
            # await self.start_conference()
            print(f"[Success]: Conference created with ID {self.conference_id}")
            # await self.keep_share()
            # print(f"share cut down or quit meeting: {self.on_meeting}")
            return f"[Success]: Conference created with ID {self.conference_id}", self.conference_id
        else:
            print(f"[Error]: Failed to create conference: {response}")
            return f"[Error]: Failed to create conference: {response}"

    async def create_p2p_conference(self, title_name):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        receive conference id.
        """
        new_conference = ConferenceServer(1, title_name)
        print("[Info]: Creating a p2p conference...")
        await new_conference.start()

    async def join_p2p_conference(self, ip):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        print(f"[Info]: Joining {ip} conference ...")
        # 这里用来讲建立交流链接，text，和命令交流
        try:
            #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            established_client, info = await connection_establish((ip, 8004))
            self.sockets['text'] = established_client
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, 8001))
            self.sockets['audio'] = sock
            print(f"[Info]: Connected to '{ip}' conference.")
            await self.keep_share()
        except Exception as e:
            print(f"[Error]: Could not connect to '{ip}' conference: {e}")


    async def join_conference(self, conference_id):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        print(f"[Info]: Joining conference {conference_id}...")
        self.conference_id = conference_id
        # 这里用来讲建立交流链接，text，和命令交流
        request_data = f"[COMMAND]: JOIN {conference_id}"
        response = await self.send_request(request_data)
        if "SUCCESS" in response:
            self.conference_id = conference_id
            self.on_meeting = True
            await self.start_conference()
            print(f"[Success]: Joined conference {self.conference_id}")
            await self.keep_share()
            print(f"share cut down or quit meeting: {self.on_meeting}")
            # return f"[Success]: CJoined conference {self.conference_id}"
        else:
            print(f"[Error]: Failed to join conference: {response}")
            return f"[Error]: Failed to join conference: {response}"

    async def quit_conference(self):
        """
        quit your ongoing conference
        """
        if not self.on_meeting:
            print("[Warn]: Not currently in any meeting.")
            return
        print("[Info]: Quitting conference...")
        request_data = f"[COMMAND]: QUIT ID {self.conference_id} {self.user_name}"
        response = await self.send_request(request_data)
        if "SUCCESS" in response:
            self.close_conference()
            self.on_meeting = False
            self.conference_id = None
            print("[Success]: Successfully quit the conference.")
        else:
            print(f"[Error]: Failed to quit conference: {response}")

    async def cancel_conference(self):
        """
        cancel your ongoing conference (when you are the conference manager): ask server to close all clients
        """
        print("[Info]: Cancelling conference...")
        request_data = f"[COMMAND]: CANCEL id {self.conference_id} {self.user_name}"
        response = await self.send_request(request_data)
        if response.startswith("SUCCESS"):
            self.close_conference()
            self.on_meeting = False
            self.conference_id = None
            print("[Success]: Conference cancelled successfully.")
        else:
            print(f"[Error]: Failed to cancel conference: {response}")

    async def start_conference(self):
        """
            init conns when create or join a conference with necessary conference_info
            and
            start necessary running task for conference
            """
        await establish_connect(self)
        print("[Info]: Initializing conference...")

    def close_conference(self):
        """
            close all conns to servers or other clients and cancel the running tasks
            pay attention to the exception handling
            """
        print("[Info]: Closing conference...")
        self.is_working = False
        self.on_meeting = False
        self.conference_id = None
        # Close all active connections

    async def send_request(self, request_data):
        """
        Send a request to the main server and receive the response.
        """
        try:
            self.established_client.send(request_data.encode())
            #writer.write(request_data.encode())
            #await writer.drain()
            response = server_response(self.established_client, None).decode("utf-8")
            #response = await reader.read(1024)
            print("test1")
            return response
        except Exception as e:
            print(f"[Error]: Failed to send request: {e}")
            return None

    async def keep_share(self, compress=None, fps_or_frequency=30):
        """
        running task: keep sharing (capture and send) certain type of data from server or clients (P2P)
        you can create different functions for sharing various kinds of data
        """
        # task_receive_text = asyncio.create_task(receive_text(self))
        # task_output = asyncio.create_task(output_data(self, fps_or_frequency))
        # task_send_text = asyncio.create_task(send_texts(self))
        # self.loop.run_in_executor(None, send_audio),  # 在独立线程中执行 send_audio
        # self.loop.run_in_executor(None, receive_audio),  # 在独立线程中执行 receive_audio
        # self.loop.run_forever()
        print("good")

        #while(self.on_meeting):
        # task_list = [asyncio.create_task(receive_text(self)), asyncio.create_task(send_texts(self)),asyncio.create_task(output_data(self, fps_or_frequency))]
        #     await asyncio.wait(task_list)
        await asyncio.gather(receive_text(self),
                                 send_texts(self, fps_or_frequency),
                             receive_audio(self, fps_or_frequency),
                             send_audio(self, fps_or_frequency),
                             send_camera(self, fps_or_frequency),
                             receive_camera(self))
                                 # asyncio.create_task(output_data(self, fps_or_frequency)))


    def share_switch(self, data_type):
        """
        switch for sharing certain type of data (screen, camera, audio, etc.)
        """
        if data_type not in self.support_data_types:
            print(f"[Warn]: Data type {data_type} is not supported.")
            return
        if data_type not in self.acting_data_types:
            self.acting_data_types[data_type] = True
            print(f"[Info]: Opening sharing for {data_type}...")
        else:
            self.acting_data_types[data_type] = False
            print(f"[Info]: Closing sharing for {data_type}...")

        # Implementation for toggling data sharing

    async def start(self):
        """
        execute functions based on the command line input
        """


if __name__ == '__main__':
    print("欢迎使用在线会议服务")
    client1 = ConferenceClient()
    established_client, info = connection_establish(client1.server_addr)
    client1.established_client = established_client
    api.app.config['CLIENT_INSTANCE'] = client1
    print("established_client:", established_client)
    print(info)
    api.app.run(debug=False)
