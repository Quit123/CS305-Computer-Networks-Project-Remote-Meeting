import asyncio
from util import *
import uuid
from asyncio import StreamReader, StreamWriter
from log_register_func import *

users = load_users(user_inf_txt)
print(users)
class ConferenceServer:
    def __init__(self, conference_id):
        # async server
        self.conference_id = conference_id  # conference_id for distinguish difference conference
        self.conf_serve_ports = 8005
        self.data_serve_ports = [8001,8002,8003,8004]
        self.data_types = ['audio','screen', 'camera','text']  # example data types in a video conference
        self.user_name = []
        self.client_conns = []
        self.servers = []
        self.online_users = 0
        self.last_online_users = 0
        self.last_join_user = "NULL"
        self.mode = 'Client-Server'  # or 'P2P' if you want to support peer-to-peer conference mode
        self.run = True

    async def handle_data(self, reader:StreamReader, writer:StreamWriter, server):
        """
        running task: receive sharing stream data from a client and decide how to forward them to the rest clients
        """
        while self.run:
            data = await reader.read(1024)
            for w in self.client_conns:
                if w != writer:
                    w.write(data)
                    await w.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_client(self, reader:StreamReader, writer:StreamWriter, message, user_name):
        """
        running task: handle the in-meeting requests or messages from clients
        """
        message = message.decode()
        parts = message.strip().spilt()
        if(parts[1]=="JOIN"):
            if(writer not in self.client_conns):
                self.client_conns.append(writer)
                self.user_name.append(user_name)
                self.online_users+=1
                self.last_join_user = user_name
                writer.write("SUCCESS join confernece".encode())
                await writer.drain()
            else:
                writer.write("FAILURE wrong user".encode())
                await writer.drain()
        elif(parts[1]=="QUIT"):
            if(writer in self.client_conns):
                self.client_conns.remove(writer)
                self.user_name.remove(user_name)
                self.last_online_users-=1
                writer.write("SUCCESS quit confernece".encode())
                await writer.drain()
            else:
                writer.write("FAILURE wrong user".encode())
                await writer.drain()                
        else:
            writer.write("FAILURE invalid command".encode())
            await writer.drain()

    async def _handle_client(self, reader:StreamReader, writer:StreamWriter, server):
        """
        running task: handle the in-meeting requests or messages from clients
        """
        ip, port = server.sockets[0].getsockname()
        print(f"connection from {ip}:{port}")
        while self.run:
            message = await reader.read(1024).decode()
            parts = message.strip().spilt()
            if(parts[0].startwith('[ASK]')):
                if(self.online_users>self.last_online_users):
                    writer.write(f"[ANS]: YES {self.last_join_user} True".encode())
                    await writer.drain()
                else:
                    writer.write("[ANS]: No False".encode())
                    await writer.drain()
                self.last_online_users = self.online_users
            else:
                print("invalid command")
                writer.write("FAILURE invalid command".encode())
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

    async def build(self):
        server = await asyncio.start_server(lambda r, w:self._handle_client(r,w,server), '127.0.0.1', 8005)
        audio_server = await asyncio.start_server(lambda r, w:self.handle_data(r,w,server), '127.0.0.1', 8001)
        screen_server = await asyncio.start_server(lambda r, w:self.handle_data(r,w,server), '127.0.0.1', 8002)
        camera_server = await asyncio.start_server(lambda r, w:self.handle_data(r,w,server), '127.0.0.1', 8003)
        text_server = await asyncio.start_server(lambda r, w:self.handle_data(r,w,server), '127.0.0.1', 8004)
        self.servers.append(server)
        self.servers.append(audio_server)
        self.servers.append(screen_server)
        self.servers.append(camera_server)
        self.servers.append(text_server)
        async with server, audio_server, screen_server, camera_server, text_server:
            await asyncio.gather(server.serve_forever(), audio_server.serve_forever(), 
                                 screen_server.serve_forever(), camera_server.serve_forever(), text_server.serve_forever())

    def start(self):
        '''
        start the ConferenceServer and necessary running tasks to handle clients in this conference
        '''
        asyncio.run(self.build(self))


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
        self.clients_info = {}  # 管理客户端加入的会议（记录该会议的）

    async def handle_creat_conference(self, writer, reader):
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client
        """
        conference_id = str(uuid.uuid4())  # 会议唯一标识
        new_conference = ConferenceServer(conference_id)  # 创建新会议服务器
        self.conference_servers[conference_id] = new_conference  # 用会议id管理会议，便于加入等操作
        self.conference_manager[conference_id] = (writer, reader)  # 用（writer, reader）唯一标识会议创建者（注：有时间的话去换成ip?）
        new_conference.start()
        writer.write(f'Conference Created: {conference_id}'.encode())  # 返回会议号
        await writer.drain()

    async def handle_join_conference(self, reader, writer, conference_id, message):
        """
        join conference: search corresponding conference_info and ConferenceServer, and reply necessary info to client
        """
        if conference_id in self.conference_servers:  # 如果可以通过会议id找到会议
            if (writer, reader)in self.clients_info:  #
                cid = self.clients_info[(writer, reader)]
                writer.write(f'You have already joined the conference {cid}'.encode())
                await writer.drain()
            else:
                conference = self.conference_servers[conference_id]
                conference.handle_client(reader, writer, message)  # 将message交给会议服务器，由会议服务器添加？
                self.clients_info[(writer, reader)] = conference_id  # 标识每个客户端加入的会议
                writer.write(f'Joined Conference: {conference_id}'.encode())
                await writer.drain()
        else:
            writer.write('Conference not found'.encode())
            await writer.drain()

    async def handle_quit_conference(self, writer, reader, message):
        """
        quit conference (in-meeting request & or no need to request)
        """
        if (writer, reader) in self.clients_info:  # 如果该用户加入了某个会议
            cid = self.clients_info[(writer, reader)]  # 用户加入的会议id
            self.conference_servers[cid].handle_client(reader, writer, message)  # 向该会议发送message
            self.clients_info.pop((writer, reader))  # 该用户未加入会议
            writer.write(f'Quit Conference: {cid}'.encode())
            await writer.drain()
        else:
            writer.write('You do not have a meeting now'.encode())
            await writer.drain()
        pass

    async def handle_cancel_conference(self, reader, writer, conference_id, message):
        """
        cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
        """
        if self.conference_manager[conference_id] == (writer, reader):  # 确认该用户是否有管理权限
            self.conference_servers[conference_id].cancel_conference()  # 有的话发送给conference_server
            self.conference_manager.pop((writer, reader))
            for (w, r) in self.conference_servers[conference_id].clients_info:  # 删除所有参加该会议的人
                self.clients_info.pop((w, r))
            self.conference_servers.pop(conference_id)  # 删除该会议
            writer.write(f'Cancel Conference: {conference_id}'.encode())
            await writer.drain()
        else:
            writer.write('Permission deny'.encode())
            await writer.drain()

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
                    print('here:'+message)
                    opera = message.split('[COMMAND]:')[1]
                    if opera.startswith('CREATE'):
                        await self.handle_creat_conference(reader, writer)
                    elif opera.startswith('JOIN'):
                        conference_id = message.split()[1]
                        await self.handle_join_conference(reader, writer, conference_id, message)
                    elif opera.startswith('QUIT'):
                        await self.handle_quit_conference(reader, writer, message)
                    elif opera.startswith('CANCEL'):
                        conference_id = opera.split()[1]
                        await self.handle_cancel_conference(reader, writer, conference_id, message)
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
