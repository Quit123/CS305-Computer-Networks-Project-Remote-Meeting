import asyncio
from util import *
from config import *


class ConferenceClient:
    def __init__(self, ):
        # sync client
        self.conference_id = None
        self.is_working = True
        self.server_addr = (SERVER_IP, MAIN_SERVER_PORT)  # server addr
        self.on_meeting = False  # status
        self.conns = None  # you may need to maintain multiple conns for a single conference
        self.support_data_types = ['screen', 'camera', 'audio']  # for some types of data
        self.running_data_types = []
        self.share_data = {}

        self.conference_info = None  # you may need to save and update some conference_info regularly

        self.recv_data = {data_type: None for data_type in ['screen', 'camera', 'audio']}
        # you may need to save received streamd data from other clients in conference

        self.reader = None
        self.writer = None

    async def establish_connection(self):
        """
        Establish a persistent connection to the server.
        """
        if not self.reader or not self.writer:
            self.reader, self.writer = await asyncio.open_connection(*self.server_addr)
            print("[Info]: Connection established with the server.")

    async def close_connection(self):
        """
        Close the persistent connection to the server.
        """
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            print("[Info]: Connection closed with the server.")
            self.reader = None
            self.writer = None

    async def send_request(self, request_data):
        """
        Send a request to the main server and receive the response.
        """
        if not self.reader or not self.writer:
            print("[Error]: Connection not established. Please ensure the connection is active.")
            return None
        try:
            self.writer.write(request_data.encode())
            await self.writer.drain()
            response = await self.reader.read(1024)
            return response.decode()
        except Exception as e:
            print(f"[Error]: Failed to send request: {e}")
            return None

    async def create_conference(self):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        receive conference id.
        """
        print("[Info]: Creating a new conference...")
        request_data = "Create Conference"
        response = asyncio.run(self.send_request(request_data))
        if response.startswith("SUCCESS"):
            # 回复格式 SUCCESS 123456
            self.conference_id = response.split()[1]
            self.on_meeting = True
            print(f"[Success]: Conference created with ID {self.conference_id}")
        else:
            print(f"[Error]: Failed to create conference: {response}")

    def join_conference(self, conference_id):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        print(f"[Info]: Joining conference {conference_id}...")
        self.conference_id = conference_id
        request_data = f"JOIN {conference_id}"
        response = asyncio.run(self.send_request(request_data))
        if response.startswith("SUCCESS"):
            self.conference_id = conference_id
            self.on_meeting = True
            print(f"[Success]: Joined conference {self.conference_id}")
        else:
            print(f"[Error]: Failed to join conference: {response}")

    def quit_conference(self):
        """
        quit your on-going conference
        """
        if not self.on_meeting:
            print("[Warn]: Not currently in any meeting.")
            return
        print("[Info]: Quitting conference...")
        request_data = f"QUIT ID {self.conference_id}"
        response = asyncio.run(self.send_request(request_data))
        if response.startswith("SUCCESS"):
            self.on_meeting = False
            self.conference_id = None
            print("[Success]: Successfully quit the conference.")
        else:
            print(f"[Error]: Failed to quit conference: {response}")

    def cancel_conference(self):
        """
        cancel your on-going conference (when you are the conference manager): ask server to close all clients
        """
        print("[Info]: Cancelling conference...")
        request_data = f"CANCEL id {self.conference_id}"
        response = asyncio.run(self.send_request(request_data))
        if response.startswith("SUCCESS"):
            self.close_conference()
            print("[Success]: Conference cancelled successfully.")
        else:
            print(f"[Error]: Failed to cancel conference: {response}")

    async def keep_share(self, data_type, send_conn, capture_function, compress=None, fps_or_frequency=30):
        """
        running task: keep sharing (capture and send) certain type of data from server or clients (P2P)
        you can create different functions for sharing various kinds of data
        """
        while self.is_working and self.on_meeting:
            data = capture_function()
            if compress:
                data = compress(data)
            send_conn.write(data)
            await send_conn.drain()
            await asyncio.sleep(1 / fps_or_frequency)

    def share_switch(self, data_type):
        """
        switch for sharing certain type of data (screen, camera, audio, etc.)
        """
        if data_type not in self.support_data_types:
            print(f"[Warn]: Data type {data_type} is not supported.")
            return
        if data_type not in self.running_data_types:
            self.running_data_types.append(data_type)
            print(f"[Info]: Opening sharing for {data_type}...")
        else:
            self.running_data_types.remove(data_type)
            print(f"[Info]: Closing sharing for {data_type}...")

        # Implementation for toggling data sharing

    async def keep_recv(self, recv_conn, data_type, decompress=None):
        """
        running task: keep receiving certain type of data (save or output)
        you can create other functions for receiving various kinds of data
        """
        while self.is_working and self.on_meeting:
            data = await recv_conn.read(1024)
            if decompress:
                data = decompress(data)
            # recv_data = Node,如何设计才能正确持续接受数据呢？
            self.recv_data[data_type] = data
            print(f"[Debug]: Received data for {data_type}")

    def output_data(self):
        """
        running task: output received stream data
        """
        while self.is_working:
            # Example for outputting received data (can be extended to handle all data types)
            if self.recv_data['screen']:
                screen_image = decompress_image(self.recv_data['screen'])
                screen_image.show()

    def start_conference(self):
        """
        init conns when create or join a conference with necessary conference_info
        and
        start necessary running task for conference
        """
        print("[Info]: Initializing conference...")
        # Initialize connections and start necessary tasks

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
            loop.run_until_complete(self.establish_connection())
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
                        if data_type in self.share_data.keys():
                            self.share_switch(data_type)
                    else:
                        recognized = False
                else:
                    recognized = False

                if not recognized:
                    print(f'[Warn]: Unrecognized cmd_input {cmd_input}')
        finally:
            # Close the connection when the application ends
            loop.run_until_complete(self.close_connection())


if __name__ == '__main__':
    client1 = ConferenceClient()
    client1.start()
