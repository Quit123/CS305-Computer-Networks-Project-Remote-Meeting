import asyncio
from util import *
import uuid


class ConferenceServer:
    def __init__(self, ):
        # async server
        self.conference_id = None  # conference_id for distinguish difference conference
        self.conf_serve_ports = None  # 会议控制通信
        self.data_serve_ports = {}
        self.data_types = ['screen', 'camera', 'audio', 'text']  # example data types in a video conference
        self.clients_info = {}  # （reader, writer）
        self.client_conns = {}
        self.mode = 'Client-Server'  # or 'P2P' if you want to support peer-to-peer conference mode
        self.run = True

    async def handle_data(self, reader, writer, data_type):
        """
        running task: receive sharing stream data from a client and decide how to forward them to the rest clients
        """

    async def handle_client(self, reader, writer):
        """
        running task: handle the in-meeting requests or messages from clients
        """

    async def log(self):
        while self.run:
            print('Something about server status')
            await asyncio.sleep(LOG_INTERVAL)

    async def cancel_conference(self):
        """
        handle cancel conference request: disconnect all connections to cancel the conference
        """

    def start(self):
        """
        start the ConferenceServer and necessary running tasks to handle clients in this conference
        """

    # def add_client(self, client_id, reader, writer):
    #     self.clients_info[client_id] = (reader, writer)
    #     self.client_conns[client_id] = writer
    #
    # def remove_client(self, client_id):
    #     if client_id in self.client_conns:
    #         del self.client_conns[client_id]


"""
MainServer 类的主要功能
管理多个会议：维护一个字典 conference_servers，其中每个键值对包含一个会议ID和对应的 ConferenceServer 实例。

处理客户端请求：负责接收来自客户端的请求，如创建会议、加入会议和退出会议，并根据请求类型将请求转发给相应的 ConferenceServer。

启动和停止会议：可以启动新的会议（通过创建 ConferenceServer 实例）和关闭会议（通过调用 ConferenceServer 的 cancel_conference 方法）。
"""


class MainServer:
    def __init__(self, server_ip, main_port):
        # async server
        self.server_ip = server_ip
        self.server_port = main_port
        self.main_server = None
        self.running = True

        self.conference_conns = None
        self.conference_servers = {}  # self.conference_servers[conference_id] = ConferenceManager
        # 每个键值对包含一个会议ID和对应的 ConferenceServer 实例
        self.conference_manager = {}  # 管理创建会议的客户端
        self.clients_info = {}  # 管理客户端加入的会议

    async def handle_creat_conference(self, writer, reader):
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client
        """
        conference_id = str(uuid.uuid4())
        new_conference = ConferenceServer()
        new_conference.conference_id = conference_id
        self.conference_conns = new_conference
        self.conference_servers[conference_id] = new_conference
        self.conference_manager[conference_id] = (writer, reader)
        new_conference.start()
        await writer.write(f'Conference Created: {conference_id}'.encode())

    async def handle_join_conference(self, reader, writer, conference_id, message):
        """
        join conference: search corresponding conference_info and ConferenceServer, and reply necessary info to client
        """
        if conference_id in self.conference_servers:
            conference = self.conference_servers[conference_id]
            conference.handle_client(reader, writer, message)
            self.clients_info[(writer, reader)] = conference_id
            await writer.write(f'Joined Conference: {conference_id}'.encode())
        else:
            await writer.write('Conference not found'.encode())

    async def handle_quit_conference(self, writer, reader, message):
        """
        quit conference (in-meeting request & or no need to request)
        """
        if (writer,reader)in self.clients_info:
            id=self.clients_info[(writer,reader)]
            self.conference_servers[id].handle_client(reader, writer, message)
            self.clients_info.pop((writer,reader))

            await writer.write(f'Quit Conference: {id}'.encode())
        else:
            await writer.write('You do not have a meeting now'.encode())
        pass

    async def handle_cancel_conference(self, reader, writer, conference_id, message):
        """
        cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
        """
        if self.conference_manager[conference_id] == (writer, reader):
            self.conference_servers[conference_id].handle_client(reader, writer, message)
            self.conference_manager.pop((writer, reader))
            for (w,r) in self.conference_servers[conference_id].clients_info:  # 删除所有参加该会议的人
                self.clients_info.pop((w,r))
            self.conference_servers.pop(conference_id)
            await writer.write(f'Cancel Conference: {conference_id}'.encode())
        else:
            await writer.write('Permission deny'.encode())

    async def request_handler(self, reader, writer):
        """
        running task: handle out-meeting (or also in-meeting) requests from clients
        """
        while self.running:
            data = await reader.read(1000)
            message = data.decode()
            if message.startswith('Create'):
                await self.handle_creat_conference(reader, writer)
            elif message.startswith('Join'):
                conference_id = message.split()[1]
                await self.handle_join_conference(reader, writer, conference_id, message)
            elif message.startswith('Quit'):
                await self.handle_quit_conference(reader, writer, message)
            elif message.startswith('Cancel'):
                conference_id = message.split()[1]
                await self.handle_cancel_conference(reader, writer, conference_id, message)

    async def start(self):
        """
        start MainServer
        """
        server = await asyncio.start_server(self.request_handler, self.server_ip, self.server_port)
        print(f'Serving on {self.server_ip}:{self.server_port}')
        await server.serve_forever()

    async def stop(self):
        for conference_id, conference in self.conference_servers.items():
            await conference.cancel_conference()
        self.running = False


if __name__ == '__main__':
    server = MainServer(SERVER_IP, MAIN_SERVER_PORT)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Server is shutting down.")
        asyncio.run(server.stop())
