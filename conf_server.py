import asyncio
from util import *
import string
from asyncio import StreamReader, StreamWriter
from log_register_func import *

users = load_users(user_inf_txt)
print(users)


class ConferenceServer:
    def __init__(self, conference_id, title):
        # async server
        self.conference_id = conference_id  # conference_id for distinguish difference conference
        self.title = title
        self.data_serve_ports = [8001, 8002, 8003, 8004]  # self.data_serve_ports=[]
        self.data_types = ['audio', 'screen', 'camera', 'text']  # example data types in a video conference
        self.user_name = []
        self.audio_conns = []
        self.screen_conns = []
        self.camera_conns = []
        self.text_conns = []
        self.servers = []
        self.online_users = 0
        self.last_online_users = 0
        self.last_join_user = "NULL"
        self.mode = 'Client-Server'  # or 'P2P' if you want to support peer-to-peer conference mode
        self.run = True
        self.tasks = []

    async def handle_data(self, reader: StreamReader, writer: StreamWriter, type):
        """
        running task: receive sharing stream data from a client and decide how to forward them to the rest clients
        """
        if type == 'audio':
            conns = self.audio_conns
        elif type == 'screen':
            conns = self.screen_conns
        elif type == 'camera':
            conns = self.camera_conns
        else:
            conns = self.text_conns
        if (writer not in conns):
            conns.append(writer)
        while self.run:
            data = await reader.read(1024)
            if type == 'text':
                print(data.decode())
            for w in conns:
                if w != writer:
                    w.write(data)
                    await w.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_client(self, reader: StreamReader, writer: StreamWriter, message):
        """
        running task: handle the in-meeting requests or messages from clients
        """
        message = message
        parts = message.strip().split(" ")
        if (parts[0].startswith('[COMMAND]')):
            if (parts[1] == "JOIN"):
                if (parts[-1] not in self.user_name):
                    self.user_name.append(parts[-1])
                    self.online_users += 1
                    self.last_join_user = parts[-1]
                    print(f"SUCCESS join confernece {self.title}")
                    writer.write(f"SUCCESS join confernece {self.title}".encode())
                    print(writer)
                    await writer.drain()
                else:
                    writer.write("FAILURE wrong user".encode())
                    await writer.drain()
            elif (parts[1] == "QUIT"):
                if (parts[-1] in self.client_conns):
                    self.user_name.remove(parts[-1])
                    self.last_online_users -= 1
                    self.online_users -= 1
                    writer.write("SUCCESS quit confernece".encode())
                    await writer.drain()
                else:
                    writer.write("FAILURE wrong user".encode())
                    await writer.drain()
            else:
                writer.write("FAILURE invalid command".encode())
                await writer.drain()
        elif (parts[0].startswith('[ASK]')):
            if (self.online_users > self.last_online_users):
                writer.write(f"[ANS]: YES {self.last_join_user} True".encode())
                await writer.drain()
            else:
                writer.write("[ANS]: No False".encode())
                await writer.drain()
            self.last_online_users = self.online_users
        else:
            print("invalid message")
            writer.write("FAILURE invalid message".encode())
            await writer.drain()

    async def log(self):
        while self.run:
            print('Something about server status')
            await asyncio.sleep(LOG_INTERVAL)

    async def cancel_conference(self):
        """
        handle cancel conference request: disconnect all connections to cancel the conference
        """
        self.run = False
        for writer in self.client_conns:
            writer.close()
            await writer.wait_closed()
        for server in self.servers:
            server.close()
            await server.wait_closed()
        self.client_conns.clear()

    # async def start_server(self, port):
    #     """
    #     为指定端口启动一个异步服务器
    #     """
    #     server = await asyncio.start_server(self.handle_data, '127.0.0.1', port)
    #     async with server:
    #         await server.serve_forever()


    async def build(self):
        print("testb1")
        self.audio_server,self.screen_server, self.camera_server, self.text_server = (
            #await self.create_udp_server(8001),
            await asyncio.start_server(lambda r, w: self.handle_data(r, w, "audio"), '10.32.111.112', 8001),
            await asyncio.start_server(lambda r, w: self.handle_data(r, w, "screen"), '10.32.111.112', 8002),
            await asyncio.start_server(lambda r, w: self.handle_data(r, w, "camera"), '10.32.111.112', 8003),
            await asyncio.start_server(lambda r, w: self.handle_data(r, w, "text"), '10.32.111.112', 8004),
            # await asyncio.start_server(lambda r, w: self.handle_data(r, w), '10.32.111.112', self.data_server_port[0]),
            # await asyncio.start_server(lambda r, w: self.handle_data(r, w), '10.32.111.112', self.data_server_port[1]),
            # await asyncio.start_server(lambda r, w: self.handle_data(r, w), '10.32.111.112', self.data_server_port[2]),
            # await asyncio.start_server(lambda r, w: self.handle_data(r, w), '10.32.111.112', self.data_server_port[3]),
        )
        print("testb2")
        # 将服务器引用保存在列表中
        self.servers = [
            self.audio_server,
            self.screen_server,
            self.camera_server,
            self.text_server,
        ]

        # 并发运行服务器
        print("testb3")
        await asyncio.gather(
            #self.UDP_server(),
            self.audio_server.serve_forever(),
            self.screen_server.serve_forever(),
            self.camera_server.serve_forever(),
            self.text_server.serve_forever(),
        )

    async def start(self):
        '''
        start the ConferenceServer and necessary running tasks to handle clients in this conference
        '''
        await self.build()


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

        # self.conference_conns = None (貌似没有用)
        self.conference_servers = {}  # self.conference_servers[conference_id] = ConferenceManager
        # 每个键值对包含一个会议ID和对应的 ConferenceServer 实例
        self.conference_manager = {}  # 管理创建会议的客户端
        self.reverse_conference_manager = {}  # conference_manager的反向映射
        self.clients_info = {}  # 管理客户端加入的会议（记录该会议的）
        self.manage_task = {}
        self.ports = [8001, 8002, 8003, 8004]

    async def handle_creat_conference(self, writer, reader, title):
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client

        """
        characters = string.ascii_letters + string.digits
        # 生成随机密码
        conference_id = ''.join(random.choice(characters) for i in range(6))  # 会议唯一标识
        print(conference_id)
        new_conference = ConferenceServer(conference_id, title)  # 创建新会议服务器
        self.conference_servers[conference_id] = new_conference  # 用会议id管理会议，便于加入等操作
        self.conference_manager[conference_id] = (writer, reader)  # 用（writer, reader）唯一标识会议创建者（注：有时间的话去换成ip?）
        self.reverse_conference_manager[(writer, reader)] = conference_id
        print("test1")
        task = asyncio.create_task(new_conference.start())
        self.manage_task[conference_id] = task
        print("test2")
        writer.write(
            f'SUCCESS {conference_id}'.encode())  # 返回会议号以及会议端口 {self.ports[0]} {self.ports[1]} {self.ports[2]} {self.ports[3]}
        print("test3")
        await writer.drain()

    async def handle_join_conference(self, reader, writer, conference_id, message):
        """
        join conference: search corresponding conference_info and ConferenceServer, and reply necessary info to client
        """
        if conference_id in self.conference_servers:  # 如果可以通过会议id找到会议
            if (writer, reader) in self.clients_info:  #
                cid = self.clients_info[(writer, reader)]
                writer.write(f'Fail:You have already joined the conference {cid}'.encode())
                await writer.drain()
            else:
                conference = self.conference_servers[conference_id]
                await conference.handle_client(reader, writer, message)  # 将message交给会议服务器，由会议服务器添加？
                self.clients_info[(writer, reader)] = conference_id  # 标识每个客户端加入的会议
                writer.write(f'SUCCESS: Joined Conference {conference_id}'.encode())
                print(conference_id)
                await writer.drain()
        else:
            writer.write('Fail: Conference not found'.encode())
            await writer.drain()

    async def handle_quit_conference(self, reader, writer, message):
        """
        quit conference (in-meeting request & or no need to request)
        """
        if (writer, reader) in self.clients_info:  # 如果该用户加入了某个会议
            if (writer, reader) in self.conference_manager:
                conference_id = self.reverse_conference_manager[(writer, reader)]
                self.conference_servers[conference_id].cancel_conference()  # 有的话发送给conference_server
                task = self.manage_task.pop(conference_id)  # Get the task associated with the conference
                task.cancel()  # Cancel the task
                self.conference_manager.pop((writer, reader))
                for (w, r) in self.conference_servers[conference_id].clients_info:  # 删除所有参加该会议的人
                    self.clients_info.pop((w, r))
                self.conference_servers.pop(conference_id)  # 删除该会议
                writer.write(f'SUCCESS: Cancel Conference: {conference_id}'.encode())
                await writer.drain()
            else:
                cid = self.clients_info[(writer, reader)]  # 用户加入的会议id
                self.conference_servers[cid].handle_client(reader, writer, message)  # 向该会议发送message
                self.clients_info.pop((writer, reader))  # 该用户未加入会议
                writer.write(f'SUCCESS: Quit Conference: {cid}'.encode())
                await writer.drain()
        else:
            writer.write('Fail: You do not have a meeting now'.encode())
            await writer.drain()
        pass

    # async def handle_cancel_conference(self, reader, writer, conference_id, message):
    #     """
    #     cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
    #     """
    #     if self.conference_manager[conference_id] == (writer, reader):  # 确认该用户是否有管理权限
    #         self.conference_servers[conference_id].cancel_conference()  # 有的话发送给conference_server
    #         task = self.manage_task.pop(conference_id)  # Get the task associated with the conference
    #         task.cancel()  # Cancel the task
    #         self.conference_manager.pop((writer, reader))
    #         for (w, r) in self.conference_servers[conference_id].clients_info:  # 删除所有参加该会议的人
    #             self.clients_info.pop((w, r))
    #         self.conference_servers.pop(conference_id)  # 删除该会议
    #         writer.write(f'SUCCESS: Cancel Conference: {conference_id}'.encode())
    #         await writer.drain()
    #     else:
    #         writer.write('Fail: Permission deny'.encode())
    #         await writer.drain()

    async def request_handler(self, reader, writer):
        """
        running task: handle out-meeting (or also in-meeting) requests from clients
        """

        with open("command.txt", "a") as f:
            while self.running:
                client_address = writer.get_extra_info('peername')
                print(f'{client_address[0]}: {client_address[1]}')
                receive_data = await reader.read(1024)
                message = receive_data.decode()
                f.write(f'{client_address}' + message + '\n')
                print(f'{client_address}:{message}')
                if message.startswith('[COMMAND]:'):
                    print('here:' + message)
                    opera = message.split(' ')[1]

                    if opera.startswith('Create'):
                        title = message.split(' ')[-2]
                        await self.handle_creat_conference(writer, reader, title)
                    elif opera.startswith('JOIN'):
                        conference_id = message.split()[2]
                        await self.handle_join_conference(reader, writer, conference_id, message)
                    elif opera.startswith('QUIT'):
                        await self.handle_quit_conference(reader, writer, message)
                else:
                    cmd = message.split(' ')
                    if cmd[0] == 'login':
                        if len(cmd) < 3:
                            feedback_data = 'Please re-enter the login commend with your username and password'
                            feedback_data = FAILURE(feedback_data)
                        elif len(cmd) == 3:
                            feedback_data, login_user = await login_authentication(writer, reader, cmd, users)
                        else:
                            feedback_data = "Password shouldn't include spaces"
                            feedback_data = FAILURE(feedback_data)
                    elif cmd[0] == 'register':
                        if len(cmd) < 3:
                            feedback_data = 'Please re-enter the command with username and password'
                            feedback_data = FAILURE(feedback_data)
                        elif len(cmd) > 3:
                            feedback_data = "Username or password shouldn't include spaces"
                            feedback_data = FAILURE(feedback_data)
                        else:
                            feedback_data = user_register(cmd, users)
                    writer.write(feedback_data.encode())
                    await writer.drain()
                    if feedback_data == '200:disconnected':
                        print(f'Client {client_address} disconnected')
                        writer.close()

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
