import asyncio
from util import *
import uuid


class ConferenceServer:
    def __init__(self, conference_id, conf_serve_ports):
        # async server
        self.conference_id = conference_id  # conference_id for distinguish difference conference
        self.conf_serve_ports = conf_serve_ports
        self.data_serve_ports = {'audio':conf_serve_ports[0],'screen':conf_serve_ports[1],'camera':conf_serve_ports[2]}
        self.data_types = ['audio','screen', 'camera']  # example data types in a video conference
        self.clients_info = []
        self.client_conns = []
        self.mode = 'Client-Server'  # or 'P2P' if you want to support peer-to-peer conference mode
        self.run = True
        self.reader = None
        self.writer = None

    async def handle_data(self, reader, writer, data_type):
        """
        running task: receive sharing stream data from a client and decide how to forward them to the rest clients
        """
        while self.run:
            data = await reader.read(1024)
            if not data:
                break
            for client_writer in self.client_conns.values():
                if client_writer != writer:
                    client_writer.write(data)
                    await client_writer.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_client(self, reader, writer):
        """
        running task: handle the in-meeting requests or messages from clients
        """
        while self.run:
            message = await reader.read(1024).decode()
            if not message:
                break
            parts = message.strip().spilt()
            if(parts[0]=="JOIN"):
                if(parts[1]==self.conference_id):
                    self.clients_info.append(parts[2])
            # Handle different types of messages here
            # For example, if a client wants to share their screen, start a handle_data task
            # if message == b'start_screen_share':
            #     asyncio.create_task(self.handle_data(reader, writer, 'screen'))
        writer.close()
        await writer.wait_closed()

    async def log(self):
        while self.run:
            print('Something about server status')
            await asyncio.sleep(LOG_INTERVAL)

    async def cancel_conference(self):
        """
        handle cancel conference request: disconnect all connections to cancel the conference
        """
        self.run = False
        for writer in self.client_conns.values():
            writer.close()
            await writer.wait_closed()
        self.client_conns.clear()

    def start(self):
        '''
        start the ConferenceServer and necessary running tasks to handle clients in this conference
        '''
        loop = asyncio.get_event_loop()
        for port in self.conf_serve_ports:
            server = asyncio.start_server(self.handle_client, '127.0.0.1', port, loop=loop)
            loop.run_until_complete(server)
        loop.create_task(self.log())
        loop.run_forever()


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
