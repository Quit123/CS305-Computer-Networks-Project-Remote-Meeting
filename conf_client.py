import queue
import struct
from conf_opt import *
from util import *
from config import *
from log_register_func import *
import api
import threading
import time
import datetime

established_client = None


class ConferenceClient:
    def __init__(self, host='127.0.0.1'):
        # sync client
        self.host = host
        self.server_addr = (SERVER_IP, MAIN_SERVER_PORT)  # server addr
        self.user_name = None
        self.log_status = False
        self.on_meeting = False  # status
        self.conference_id = None
        self.support_data_types = ['text', 'audio', 'camera']
        #self.support_data_types = ['screen', 'camera', 'audio', 'text']  # for some types of data
        self.acting_data_types = {data_type: False for data_type in ['screen', 'camera', 'audio']}
        self.acting_data_types['text'] = True  # 这里使用前端控制，delete
        self.acting_data_types['audio'] = True
        self.acting_data_types['camera'] = False
        self.ports = {'audio': 0, 'screen': 0, 'camera': 0, 'text': 0}
        # 用来存不同类型的socket
        self.sockets = {}
        self.camera_queues = {}
        self.camera_last = {}
        self.camera_threads = {}  # 存储每个成员对应的线程
        self.text = None
        self.can_share_screen = True
        self.conference_info = None  # you may need to save and update some conference_info regularly
        self.established_client = None
        self.frame = None
        self.cap = None
        self.stream = None
        self.conference_type = 1
        self.p2p_initiator = False
        self.multi_initiator = False
        self.create_status = 0

    def check_status(self):
        while self.create_status == 0:
            time.sleep(0.1)
            print("checking")
        if self.create_status == 1:
            self.keep_share()
        else:
            print("join conference failed")

    def set_ports(self, response, type):
        if type == 1:
            port_num = int(response.split()[-1])
            self.ports['audio'] = port_num
            self.ports['screen'] = port_num + 1
            self.ports['camera'] = port_num + 2
            print("camera port:", self.ports['camera'])
            self.ports['text'] = port_num + 3
        else:
            self.ports['audio'] = 8001
            self.ports['screen'] = 8002
            self.ports['camera'] = 8003
            self.ports['text'] = 8004

    def create_conference(self, title_name, type):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        receive conference id.
        """
        print("[Info]: Creating a new conference...")
        request_data = None
        if type == 1:
            request_data = f"[COMMAND]: Create Conference {title_name}"
        else:
            request_data = f"[COMMAND]: Create P2P Conference {title_name}"
        # 这里用来讲建立交流链接，text，和命令交流
        print(request_data)
        response = self.send_request(request_data)
        print("recv create response:", response)
        if "SUCCESS" in response:

            # check_join_thread = threading.Thread(target=self.check_status)
            # check_join_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
            # check_join_thread.start()

            # 回复格式 SUCCESS 123456
            self.conference_id = response.split()[1]
            self.set_ports(response, type)
            if type == 2:
                ip_address = response.split()[-1]
                self.server_addr = (ip_address, self.server_addr[1])
            self.on_meeting = True
            # await self.start_conference()
            print(f"[Success]: Conference created with ID {self.conference_id}")
            # await self.keep_share()
            # print(f"share cut down or quit meeting: {self.on_meeting}")
            return f"[Success]: Conference created with ID {self.conference_id}", self.conference_id
        else:
            print(f"[Error]: Failed to create conference: {response}")
            return f"[Error]: Failed to create conference: {response}"

    def join_conference(self, conference_id, type):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        print(f"[Info]: Joining conference {conference_id}...")
        self.conference_id = conference_id

        # if not self.multi_initiator and not self.p2p_initiator:
        #     check_join_thread = threading.Thread(target=self.check_status)
        #     check_join_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        #     check_join_thread.start()

        # 这里用来讲建立交流链接，text，和命令交流
        request_data = f"[COMMAND]: JOIN {conference_id}"
        print(request_data)
        response = self.send_request(request_data)
        if "SUCCESS" in response:
            if self.ports['audio'] == 0:
                self.set_ports(response, type)
            if type == 2 and not self.p2p_initiator:
                ip_address = response.split()[-1]
                self.server_addr = (ip_address, self.server_addr[1])
            self.conference_id = conference_id
            self.on_meeting = True
            self.start_conference()
            self.keep_share()
            # self.create_status = 1
            print(f"[Success]: Joined conference {self.conference_id}")
            return f"[Success]: Joined conference {self.conference_id}"
        else:
            print(f"[Error]: Failed to join conference: {response}")
            return f"[Error]: Failed to join conference: {response}"

    def quit_conference(self):
        """
        quit your ongoing conference
        """
        if not self.on_meeting:
            print("[Warn]: Not currently in any meeting.")
            return
        print("[Info]: Quitting conference...")
        request_data = f"[COMMAND]: QUIT ID {self.conference_id} {self.user_name}"
        response = self.send_request(request_data)
        if "SUCCESS" in response:
            self.close_conference()
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
        self.on_meeting = False
        self.conference_id = None
        self.p2p_initiator = False
        self.multi_initiator = False
        self.conference_type = 1
        self.create_status = 0
        self.cap.close()
        self.stream.close()
        # Close all active connections

    def send_request(self, request_data):
        """
        Send a request to the main server and receive the response.
        """
        try:
            self.established_client.send(request_data.encode())
            response = server_response(self.established_client, None).decode("utf-8")
            return response
        except Exception as e:
            print(f"[Error]: Failed to send request: {e}")
            return None

    def keep_share(self, compress=None, fps_or_frequency=30):
        """
        running task: keep sharing (capture and send) certain type of data from server or clients (P2P)
        you can create different functions for sharing various kinds of data
        """
        print("good")

        self.send_info()
        self.recv_info()

    def send_info(self):
        """Capture, compress, and send camera image to the server."""
        send_text_thread = threading.Thread(target=self.send_texts)
        send_text_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        send_text_thread.start()

        send_audio_thread = threading.Thread(target=self.send_audio)
        send_audio_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        send_audio_thread.start()

        send_camera_thread = threading.Thread(target=self.send_camera)
        send_camera_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        send_camera_thread.start()

    def recv_info(self):
        recv_audio_thread = threading.Thread(target=self.receive_audio)
        recv_audio_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        recv_audio_thread.start()

        recv_text_thread = threading.Thread(target=self.receive_text)
        recv_text_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        recv_text_thread.start()

        recv_camera_thread = threading.Thread(target=self.receive_camera_main)
        recv_camera_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        recv_camera_thread.start()

    def send_texts(self):
        print("run send text")
        socket_text = self.sockets['text']
        while self.on_meeting:
            # print("[Info]: Sending text...")
            if self.text:
                print("[Info]: Updating text...")
                print(f"[Info]: Sending: {self.text}")

                message = b''
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                timestamp_bytes = current_time.encode('utf-8')
                user_bytes = self.user_name.encode('utf-8')
                text_bytes = self.text.encode('utf-8')
                message += timestamp_bytes + user_bytes + b'?' * (8 - len(user_bytes)) + text_bytes

                target_address = self.server_addr[0]  # 目标服务器的 IP 地址
                port = self.ports.get('text')  # 获取对应的端口
                #established_text.send(self.text.encode('utf-8'))
                socket_text.sendto(message, (target_address, port))
                self.text = None

    def send_audio(self):
        try:
            self.stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            socket_audio = self.sockets['audio']
            target_address = self.server_addr[0]  # 目标服务器的 IP 地址
            port = self.ports.get('audio')  # 获取对应的端口
            print("run send audio")
            while self.on_meeting:
                if self.acting_data_types['audio']:
                    if self.stream is None:
                        self.stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
                    try:
                        data = self.stream.read(CHUNK)
                        if not data:
                            continue
                        try:
                            socket_audio.sendto(data, (target_address, port))
                        except socket.error as e:
                            print(f"[Error]: Socket error during audio send: {e}")
                    except socket.error as e:
                        print(f"[Error]: Socket error during audio send: {e}")
                        # 处理连接错误，可以重新尝试连接或退出
                        break  # 连接中断，退出循环
                    except Exception as e:
                        print(f"[Error]: Unexpected error during audio send: {e}")
                        break  # 捕获其他异常，退出循环
                else:
                    self.stream.close()  # 关闭流
                    self.stream = None
        except Exception as e:
            print(f"[Error]: Error in send_audio: {e}")

    def send_camera_(self):
        camera_socket = self.sockets['camera']
        target_address = self.server_addr[0]  # 目标服务器的 IP 地址
        port = self.ports.get('camera')  # 获取对应的端口
        while self.on_meeting:
            if self.acting_data_types['camera']:
                # if self.acting_data_types['camera']:
                #     print("running send_camera")
                if not self.cap.isOpened():
                    cap = cv2.VideoCapture(0)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
                ret, frame = self.cap.read()  # 获取图像

                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 20]
                img_encode = cv2.imencode('.jpg', frame, encode_param)[1]
                data_encode = np.array(img_encode)
                image_data = data_encode.tobytes()
                camera_socket.sendto(image_data, (target_address, port))
        else:
            self.cap.release()

    def send_camera(self):
        camera_socket = self.sockets['camera']
        target_address = self.server_addr[0]  # 目标服务器的 IP 地址
        port = self.ports.get('camera')  # 获取对应的端口
        repeat = 0
        while self.on_meeting:
            if self.acting_data_types['camera']:
                if self.cap is None:
                    repeat = 0
                    self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 设置缓冲区大小为 1 帧
                    # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
                    # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
                    self.cap.set(cv2.CAP_PROP_FPS, 10)  # 设置较低的帧率
                ret, frame = self.cap.read()
                try:
                    if ret:
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 20]
                        img_encode = cv2.imencode('.jpg', frame, encode_param)[1]
                        #img_encode = cv2.imencode('.jpg', frame)[1]
                        data_encode = np.array(img_encode)
                        image_data = data_encode.tobytes()

                        message = b''
                        user_bytes = self.user_name.encode('utf-8')
                        message += user_bytes + b'\0' * (8 - len(user_bytes)) + image_data
                        camera_socket.sendto(message, (target_address, port))
                except ConnectionAbortedError as e:
                    print(f"[Error]: Connection aborted: {e}")
            else:
                if repeat == 0:
                    black_frame = np.zeros((camera_height, camera_width, 3), dtype=np.uint8)
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 5]
                    img_encode = cv2.imencode('.jpg', black_frame, encode_param)[1]
                    image_data = img_encode.tobytes()

                    message = b''
                    user_bytes = self.user_name.encode('utf-8')
                    message += user_bytes + b'\0' * (8 - len(user_bytes)) + image_data
                    camera_socket.sendto(message, (target_address, port))
                    repeat = 1
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None

    def receive_text(self, decompress=None):
        socket_text = self.sockets['text']
        # while self.on_meeting:
        if not socket_text:
            print("[Info]: 初始化失败")
        print("[Info]: Starting text playback monitoring...")
        while self.on_meeting:
            recv_data, addr = socket_text.recvfrom(1024)
            if recv_data:
                time = recv_data[:19]
                time = time.decode('utf-8')
                user_name = recv_data[19:27]  # 前8个字符
                user_name = user_name.rstrip(b'?')
                # user_name = user_name.strip('\0')  # 解码并去掉填充的 '\0'
                user_name = user_name.decode('utf-8')
                recv_text = recv_data[27:]
                recv_text = recv_text.decode('utf-8')
                print(recv_text)
                # 主动给前端发送信息，使用 emit 来发送自定义事件
                # api.send_text({"message": recv_text})
                api.recv_text(time, user_name, recv_text)
                print("receive message:", recv_text)

    def receive_audio(self):
        try:
            BUFF_SIZE = 65536
            socket_audio = self.sockets['audio']
            streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
            print("Run into audio")
            while self.on_meeting:
                # recv_data, addr = socket_audio.recvfrom(BUFF_SIZE)
                # streamout.write(recv_data)
                try:
                    # 接收音频数据
                    recv_data, addr = socket_audio.recvfrom(BUFF_SIZE)
                    streamout.write(recv_data)
                    # print("Received audio data")
                except ConnectionAbortedError as e:
                    print(f"[Error]: Connection aborted: {e}")
                    break
        except Exception as e:
            print(f"[Error]: An error occurred in receive_audio: {e}")

    def start_camera_thread(self, user):
        """为每个新用户启动一个线程"""
        if user not in self.camera_threads:
            # 为新用户启动线程
            recv_camera_thread = threading.Thread(target=self.receive_camera, args=(user,))
            recv_camera_thread.daemon = True  # 设置为守护线程
            recv_camera_thread.start()

            # 将新线程存储在字典中，方便管理
            self.camera_threads[user] = recv_camera_thread
            print(f"为用户 {user} 启动了一个线程")

    def receive_camera_main(self):
        try:
            socket_camera = self.sockets['camera']
            print("Run into camera")
            while self.on_meeting:
                # print("waiting address")
                recv_data, addr = socket_camera.recvfrom(400000)

                user_name = recv_data[:8]  # 前8个字符
                user = user_name.decode('utf-8').strip('\0')  # 解码并去掉填充的 '\0'
                if user not in self.camera_queues:
                    self.camera_last[user] = None
                    self.start_camera_thread(user)

                if user == self.user_name:
                    camera_data = recv_data[8:]  # 后面的数据
                    api.recv_camera(self.user_name, camera_data)

                    # self.frame = img_decode
        except Exception as e:
            print(f"[Error]: An error occurred in receive_camera: {e}")

    def receive_camera(self, default_user):
        try:
            socket_audio = self.sockets['camera']
            print("Run into camera")
            while self.on_meeting:
                # print("waiting address")
                recv_data, addr = socket_audio.recvfrom(400000)

                user_name = recv_data[:8]  # 前8个字符
                user = user_name.decode('utf-8').strip('\0')  # 解码并去掉填充的 '\0'
                if user == default_user:
                    camera_data = recv_data[8:]  # 后面的数据
                    nparr = np.frombuffer(camera_data, np.uint8)
                    camera_data_bytes = nparr.tobytes()
                    self.camera_last[default_user] = camera_data_bytes
                    api.recv_camera(default_user, camera_data_bytes)

        except Exception as e:
            print(f"[Error]: An error occurred in receive_camera: {e}")

    def receive_camera_(self, decompress=None):
        print("[Info]: Starting camera playback monitoring...")
        # loop = asyncio.get_event_loop()
        camera_socket = self.sockets['camera']
        # while self.on_meeting:
        if not camera_socket:
            print("[info]: camera 初始化失败")

        user_bytes, addr = camera_socket.recvfrom(16)
        user = user_bytes.decode('utf-8').strip('\0')  # 解码并去掉填充的 '\0'

        if user not in self.camera_queues:
            self.camera_queues[user] = queue.Queue()
            self.camera_last[user] = None

        image_length_bytes, addr = camera_socket.recvfrom(4)
        image_length = struct.unpack('!I', image_length_bytes)[0]  # 解包得到图像的字节长度

        image_bytes = camera_socket.recvfrom(image_length)

        image = decompress_image(image_bytes)
        self.camera_queues[user].put(image)
        self.camera_last[user] = image

    def share_switch(self, data_type):
        """
        switch for sharing certain type of data (screen, camera, audio, etc.)
        """
        if data_type not in self.support_data_types:
            print(f"[Warn]: Data type {data_type} is not supported.")
            return
        if self.acting_data_types[data_type]:
            self.acting_data_types[data_type] = False
            print(f"[Info]: Closing sharing for {data_type}...")
        else:
            self.acting_data_types[data_type] = True
            print(f"[Info]: Opening sharing for {data_type}...")

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
