import asyncio
import util
from conf_opt import *
from util import *
from config import *


class ConferenceClient:
    def __init__(self, host='127.0.0.1'):
        # sync client
        self.host = host
        self.support_data_types = ['screen', 'camera', 'audio', 'text']  # for some types of data
        self.acting_data_types = {data_type: False for data_type in ['screen', 'camera', 'audio', 'text']}
        self.acting_data_types['text'] = True
        self.ports = {'audio': 8001, 'screen': 8002, 'camera': 8003, 'text': 8004}
        # 初始化字典
        self.sockets = {}
        # you may need to save received streamd data from other clients in conference
        self.data_queues = {data_type: asyncio.Queue() for data_type in ['screen', 'camera', 'audio', 'text']}

        self.server_addr = (SERVER_IP, MAIN_SERVER_PORT)  # server addr
        self.conference_id = None
        self.is_working = True
        self.on_meeting = False  # status
        self.conference_info = None  # you may need to save and update some conference_info regularly

    def create_conference(self):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        receive conference id.
        """
        print("[Info]: Creating a new conference...")
        request_data = "COMMAND: Create Conference"
        response = asyncio.run(self.send_request(request_data))
        if response.startswith("SUCCESS"):
            # 回复格式 SUCCESS 123456
            self.conference_id = response.split()[1]
            self.start_conference()
            self.on_meeting = True
            self.keep_share()
            print(f"[Success]: Conference created with ID {self.conference_id}")
        else:
            print(f"[Error]: Failed to create conference: {response}")

    def join_conference(self, conference_id):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        print(f"[Info]: Joining conference {conference_id}...")
        self.conference_id = conference_id
        request_data = f"COMMAND: JOIN {conference_id}"
        response = asyncio.run(self.send_request(request_data))
        if response.startswith("SUCCESS"):
            self.conference_id = conference_id
            self.start_conference()
            self.on_meeting = True
            self.keep_share()
            print(f"[Success]: Joined conference {self.conference_id}")
        else:
            print(f"[Error]: Failed to join conference: {response}")

    def quit_conference(self):
        """
        quit your ongoing conference
        """
        if not self.on_meeting:
            print("[Warn]: Not currently in any meeting.")
            return
        print("[Info]: Quitting conference...")
        request_data = f"COMMAND: QUIT ID {self.conference_id}"
        response = asyncio.run(self.send_request(request_data))
        if response.startswith("SUCCESS"):
            self.close_conference()
            self.on_meeting = False
            self.conference_id = None
            print("[Success]: Successfully quit the conference.")
        else:
            print(f"[Error]: Failed to quit conference: {response}")

    def cancel_conference(self):
        """
        cancel your ongoing conference (when you are the conference manager): ask server to close all clients
        """
        print("[Info]: Cancelling conference...")
        request_data = f"COMMAND: CANCEL id {self.conference_id}"
        response = asyncio.run(self.send_request(request_data))
        if response.startswith("SUCCESS"):
            self.close_conference()
            self.on_meeting = False
            self.conference_id = None
            print("[Success]: Conference cancelled successfully.")
        else:
            print(f"[Error]: Failed to cancel conference: {response}")

    def start_conference(self):
        """
            init conns when create or join a conference with necessary conference_info
            and
            start necessary running task for conference
            """
        establish_connect(self)
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
        if not self.sockets['text']:
            print("[Error]: Connection not established. Please ensure the connection is active.")
            return None
        try:
            reader, writer = self.sockets['text']
            writer.write(request_data.encode())
            await writer.drain()
            response = await reader.read(1024)
            return response.decode()
        except Exception as e:
            print(f"[Error]: Failed to send request: {e}")
            return None

    async def keep_share(self, compress=None, fps_or_frequency=30):
        """
        running task: keep sharing (capture and send) certain type of data from server or clients (P2P)
        you can create different functions for sharing various kinds of data
        """
        # 启动任务并立即返回
        asyncio.create_task(receive_audio(self))
        asyncio.create_task(output_audio(self, fps_or_frequency))
        # 上为初始化，负责接受和输出各类数据
        # 下为控制数据发送
        while self.is_working and self.on_meeting:
            if self.acting_data_types['text']:
                pass
            if self.acting_data_types['audio']:
                asyncio.create_task(send_audio(self))
            if self.acting_data_types['video']:
                pass
            if self.acting_data_types['audio']:
                pass

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

    def start(self):
        """
        execute functions based on the command line input
        """
        # 获取当前运行的事件循环（Event Loop）
        # 事件循环是异步编程的核心，它协调并调度所有的异步任务和操作。
        # 如果当前线程没有运行中的事件循环，它会创建一个新的事件循环并返回。
        loop = asyncio.get_event_loop()
        try:
            # Establish the connection at the start of the application
            # loop.run_until_complete(self.establish_connect())
            # run_until_complete(coro) 是事件循环的一个方法，用于运行一个协程并阻塞程序，直到协程执行完成。
            # Command-line interface
            while True:
                if not self.on_meeting:
                    status = 'Free'
                else:
                    status = f'OnMeeting-{self.conference_id}'

                recognized = True
                cmd_input = input(f'({status}) Please enter an operation (enter "?" to help): ').strip().lower()
                fields = cmd_input.split(maxsplit=1)
                if len(fields) == 1:
                    if cmd_input in ('?', '？'):
                        print(HELP)
                    elif cmd_input == 'create':
                        self.create_conference()
                    elif cmd_input == 'quit':
                        self.quit_conference()
                    elif cmd_input == 'cancel':
                        self.cancel_conference()
                    else:
                        recognized = False
                elif len(fields) == 2:
                    if fields[0] == 'join':
                        input_conf_id = fields[1]
                        if input_conf_id.isdigit():
                            self.join_conference(input_conf_id)
                        else:
                            print('[Warn]: Input conference ID must be in digital form')
                    elif fields[0] == 'switch':
                        data_type = fields[1]
                        self.share_switch(data_type)
                    else:
                        recognized = False
                else:
                    recognized = False

                if not recognized:
                    print(f'[Warn]: Unrecognized cmd_input {cmd_input}')
        except Exception as e:
            print("[Warn]: Exception occurred:\n", e)
        # Close the connection when the application ends


if __name__ == '__main__':
    client1 = ConferenceClient()
    client1.start()
