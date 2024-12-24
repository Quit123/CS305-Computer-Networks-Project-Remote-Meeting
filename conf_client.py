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
        self.support_data_types = ['text', 'audio', 'camera', 'screen']
        #self.support_data_types = ['screen', 'camera', 'audio', 'text']  # for some types of data
        self.acting_data_types = {data_type: False for data_type in ['screen', 'camera', 'audio', 'screen']}
        self.acting_data_types['text'] = True  # 这里使用前端控制，delete
        self.acting_data_types['audio'] = True
        self.acting_data_types['camera'] = False
        self.acting_data_types['screen'] = False
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
        self.host = False
        self.allow_quit = False
        self.thread_management = []
        self.main_thread = []
        self.recv_thread = []

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

    def join_conference(self, conference_id):
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
            if "P2P" in response:
                self.conference_type = 2
            if self.ports['audio'] == 0:
                self.set_ports(response, self.conference_type)
            if self.conference_type == 2 and not self.p2p_initiator:
                self.server_addr = (response.split()[-1], self.server_addr[1])
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
        if self.conference_type == 1:
            request_data = f"[COMMAND]: QUIT ID {self.conference_id} {self.user_name}"
        else:
            request_data = f"[COMMAND]: QUIT P2P ID{self.user_name} {self.conference_id}"
        self.established_client.sendall(request_data.encode())

        # response = self.send_request(request_data)
        # if "SUCCESS" in response:
        #     self.close_conference()
        #     print("[Success]: Successfully quit the conference.")
        # else:
        #     print(f"[Error]: Failed to quit conference: {response}")

    def cancel_conference(self):
        """
        cancel your ongoing conference (when you are the conference manager): ask server to close all clients
        """
        print("[Info]: Cancelling conference...")
        if self.conference_type == 1:
            request_data = f"[COMMAND]: CANCEL id {self.conference_id} {self.user_name}"
        else:
            request_data = f"[COMMAND]: CANCEL P2P id {self.conference_id} {self.user_name}"

        self.established_client.sendall(request_data.encode())
        # response = await self.send_request(request_data)
        # if response.startswith("SUCCESS"):
        #     self.close_conference()
        #     print("[Success]: Conference cancelled successfully.")
        # else:
        #     print(f"[Error]: Failed to cancel conference: {response}")

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
        for t in self.thread_management:
            t.join()
        print("[Success]: send thread closed")
        if self.conference_type == 2:
            text_bytes = "QUIT".encode('utf-8')
            for i in range(3):
                self.sockets['text'].sendto(text_bytes, (self.server_addr[0], 8004))
                self.sockets['audio'].sendto(text_bytes, (self.server_addr[0], 8001))
                self.sockets['screen'].sendto(text_bytes, (self.server_addr[0], 8002))
                self.sockets['camera'].sendto(text_bytes, (self.server_addr[0], 8003))
        time.sleep(0.5)
        for t in self.recv_thread:
            t.join()
        self.conference_id = None
        self.p2p_initiator = False
        self.multi_initiator = False
        self.acting_data_types['text'] = True  # 这里使用前端控制，delete
        self.acting_data_types['audio'] = True
        self.acting_data_types['camera'] = False
        self.acting_data_types['screen'] = False
        self.thread_management = []
        self.ports = {'audio': 0, 'screen': 0, 'camera': 0, 'text': 0}
        for s in self.sockets.values():
            s.close()
        self.sockets.clear()
        self.sockets = {}

        self.text = None
        self.camera_queues = {}
        self.camera_last = {}
        self.camera_threads = {}

        self.host = False
        self.can_share_screen = True
        self.allow_quit = False

        self.conference_type = 1
        self.create_status = 0

        if self.cap is not None:
            self.cap.release()
        if self.stream is not None:
            self.stream.close()

        print("conference has closed")
        # Close all active connections

        # 用来存不同类型的socket
        # 存储每个成员对应的线程


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
        recv_change_info = threading.Thread(target=self.recv_host)
        recv_change_info.daemon = True  # 设置为守护线程，程序退出时自动关闭
        recv_change_info.start()
        # self.main_thread.append(recv_change_info)
        # self.thread_management.append(recv_change_info)

    def recv_host(self):
        while self.on_meeting:
            info = established_client.recv(1024).decode()
            if "HOST" in info:
                print("[Info]: You are host")
                api.recv_host_info(info)
                self.host = True
            if "QUIT" in info:
                # 前端主动退出，应该不需要api.recv_quit(info)
                print("[Info]: Quit is running")
                api.recv_quit(info)
                self.allow_quit = True
                self.close_conference()
            if "CANCEL FAIL" in info:
                print("[Info]: You are not host")
                self.allow_quit = False
            if "SUCCESS SCREEN" in info:
                self.acting_data_types["screen"] = True
                print("screen is sharing")
            if "FAIL SCREEN" in info:
                self.acting_data_types["screen"] = False
                print("screen can't share")
            time.sleep(0.1)


    def send_info(self):
        """
        Capture, compress, and send camera image to the server.
        """
        # send_text_thread = threading.Thread(target=self.send_texts)
        # send_text_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        # send_text_thread.start()

        send_audio_thread = threading.Thread(target=self.send_audio_text)
        send_audio_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        send_audio_thread.start()
        self.thread_management.append(send_audio_thread)

        send_camera_thread = threading.Thread(target=self.send_camera)
        send_camera_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        send_camera_thread.start()
        self.thread_management.append(send_camera_thread)
        # send_screen_thread = threading.Thread(target=self.send_screen)
        # send_screen_thread.daemon = True
        # send_screen_thread.start()

    def recv_info(self):
        recv_audio_thread = threading.Thread(target=self.receive_audio)
        recv_audio_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        recv_audio_thread.start()
        self.recv_thread.append(recv_audio_thread)

        recv_text_thread = threading.Thread(target=self.receive_text)
        recv_text_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        recv_text_thread.start()
        self.recv_thread.append(recv_text_thread)

        recv_camera_thread = threading.Thread(target=self.receive_camera_main)
        recv_camera_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        recv_camera_thread.start()
        self.recv_thread.append(recv_camera_thread)

        recv_screen_thread = threading.Thread(target=self.receive_screen)
        recv_screen_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        recv_screen_thread.start()
        self.recv_thread.append(recv_screen_thread)

    def send_texts(self):
        socket_text = self.sockets['text']
        print("run function of send text")
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

    def send_audio_text(self):
        try:
            self.stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            socket_audio = self.sockets['audio']
            socket_text = self.sockets['text']
            # socket_camera = self.sockets['camera']
            repeat = 0
            target_address = self.server_addr[0]  # 目标服务器的 IP 地址
            port_audio = self.ports.get('audio')  # 获取对应的端口
            port_text = self.ports.get('text')  # 获取对应的端口
            # port_camera = self.ports.get('camera')  # 获取对应的端口
            print("run function of send text")
            print("run function of send audio")
            while self.on_meeting:
                if self.acting_data_types['audio']:
                    if self.stream is None:
                        self.stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
                    try:
                        data = self.stream.read(CHUNK)
                        if not data:
                            continue
                        try:
                            socket_audio.sendto(data, (target_address, port_audio))
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
                    if self.stream is not None:
                        self.stream.close()  # 关闭流
                        self.stream = None

                if self.text:

                    print(f"[Info]: Sending: {self.text}")
                    message = b''
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    timestamp_bytes = current_time.encode('utf-8')
                    user_bytes = self.user_name.encode('utf-8')
                    text_bytes = self.text.encode('utf-8')
                    message += timestamp_bytes + user_bytes + b'?' * (8 - len(user_bytes)) + text_bytes

                    # target_address = self.server_addr[0]  # 目标服务器的 IP 地址
                    # established_text.send(self.text.encode('utf-8'))
                    socket_text.sendto(message, (target_address, port_text))
                    self.text = None
        except Exception as e:
            print(f"[Error]: Error in send_audio_text: {e}")

    def send_screen(self):
        socket_screen = self.sockets['screen']
        target_address = self.server_addr[0]  # 目标服务器的 IP 地址
        port = self.ports.get('screen')  # 获取对应的端口
        print("run function of send screen")
        while self.on_meeting:
            if self.acting_data_types['screen']:
                img = pyautogui.screenshot()
                img = np.array(img)
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
                img_encoded = cv2.imencode('.jpg', img, encode_param)[1]
                compressed_image_data = img_encoded.tobytes()
                api.recv_screen(compressed_image_data)
                socket_screen.sendto(compressed_image_data, (target_address, port))

    def send_camera(self):
        try:
            target_address = self.server_addr[0]  # 目标服务器的 IP 地址
            camera_socket = self.sockets['camera']
            port_camera = self.ports.get('camera')  # 获取对应的端口
            socket_screen = self.sockets['screen']
            port_screen = self.ports.get('screen')  # 获取对应的端口
            repeat = 0
            repeat_sc = 0
            frame_counter = 0
            max_udp_size = 65000
            print("run function of send screen")
            print("run function of send camera")

            while self.on_meeting:
                if self.acting_data_types['camera']:
                    if self.cap is None:
                        repeat = 0
                        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 设置缓冲区大小为 1 帧
                        self.cap.set(cv2.CAP_PROP_FPS, 10)  # 设置较低的帧率
                    ret, frame = self.cap.read()
                    try:
                        if ret:
                            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 20]
                            img_encode = cv2.imencode('.jpg', frame, encode_param)[1]
                            data_encode = np.array(img_encode)
                            image_data = data_encode.tobytes()
                            # 个人显示
                            api.recv_camera(self.user_name, image_data)

                            message = b''
                            user_bytes = self.user_name.encode('utf-8')
                            message += user_bytes + b'\0' * (8 - len(user_bytes)) + image_data
                            camera_socket.sendto(message, (target_address, port_camera))
                    except ConnectionAbortedError as e:
                        print(f"[Error]: Connection aborted: {e}")
                else:
                    if repeat <= 3:
                        black_frame = np.zeros((camera_height, camera_width, 3), dtype=np.uint8)
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 5]
                        img_encode = cv2.imencode('.jpg', black_frame, encode_param)[1]
                        image_data = img_encode.tobytes()
                        # 个人显示
                        api.recv_camera(self.user_name, image_data)

                        message = b''
                        user_bytes = self.user_name.encode('utf-8')
                        message += user_bytes + b'\0' * (8 - len(user_bytes)) + image_data
                        camera_socket.sendto(message, (target_address, port_camera))
                        repeat = repeat + 1
                    if self.cap is not None:
                        self.cap.release()
                        self.cap = None

                if self.acting_data_types['screen']:
                    img = pyautogui.screenshot()  # 获取屏幕截图
                    img = np.array(img)  # 转换为 NumPy 数组
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
                    img_encoded = cv2.imencode('.jpg', img, encode_param)[1]
                    compressed_image_data = img_encoded.tobytes()  # 获取压缩后的字节数据

                    api.recv_screen(compressed_image_data)

                    if frame_counter >= 65530:
                        frame_counter = 0
                    # 计算分块大小，保持每个块的大小适合 UDP 传输
                    if len(compressed_image_data) > max_udp_size:
                        # print(f"Data size {len(compressed_image_data)} exceeds max UDP size, splitting...")
                        for i in range(0, len(compressed_image_data), max_udp_size):
                            chunk = compressed_image_data[i:i + max_udp_size]
                            # 生成16位标识符（frame_counter）并打包为2字节
                            identifier = (frame_counter & 0xFFFF).to_bytes(2, byteorder='big')
                            # 拼接标识符和数据块
                            chunk_with_identifier = identifier + chunk
                            # 发送数据块
                            socket_screen.sendto(chunk_with_identifier, (target_address, port_screen))
                        # 增加帧计数器
                        frame_counter += 1
                    else:
                        # 对于小于最大 UDP 大小的数据，直接发送
                        identifier = (frame_counter & 0xFFFF).to_bytes(2, byteorder='big')
                        chunk_with_identifier = identifier + compressed_image_data
                        socket_screen.sendto(chunk_with_identifier, (target_address, port_screen))
                        # 增加帧计数器
                        frame_counter += 1
                else:
                    if repeat_sc < 3:
                        # 如果为False，发送全黑色图像
                        height, width = 1080, 1920  # 假设屏幕大小为 1920x1080
                        black_image = np.zeros((height, width, 3), dtype=np.uint8)  # 创建一个全黑图像
                        # 设置 JPEG 压缩质量
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
                        img_encoded = cv2.imencode('.jpg', black_image, encode_param)[1]
                        compressed_image_data = img_encoded.tobytes()  # 获取压缩后的字节数据
                        # 发送全黑图像
                        if frame_counter >= 65530:
                            frame_counter = 0
                        if len(compressed_image_data) > max_udp_size:
                            for i in range(0, len(compressed_image_data), max_udp_size):
                                chunk = compressed_image_data[i:i + max_udp_size]
                                identifier = (frame_counter & 0xFFFF).to_bytes(2, byteorder='big')
                                chunk_with_identifier = identifier + chunk
                                socket_screen.sendto(chunk_with_identifier, (target_address, port_screen))
                            frame_counter += 1
                        else:
                            identifier = (frame_counter & 0xFFFF).to_bytes(2, byteorder='big')
                            chunk_with_identifier = identifier + compressed_image_data
                            socket_screen.sendto(chunk_with_identifier, (target_address, port_screen))
                            frame_counter += 1
                        repeat_sc = repeat_sc + 1
        except ConnectionAbortedError as e:
            print(f"[Error]: Connection aborted: {e}")


    def receive_text(self, decompress=None):
        socket_text = self.sockets['text']
        close = False
        if not socket_text:
            print("[Info]: 初始化失败")
        print("[Info]: Starting text playback monitoring...")
        while self.on_meeting and not close:
            if not socket_text or not isinstance(socket_text, socket.socket):
                time.sleep(0.5)
                print("waiting recv text")
            else:
                try:
                    recv_data, addr = socket_text.recvfrom(1024)
                    if b'QUIT' in recv_data:
                        close = True
                        print("close recv text thread stage1")
                        continue
                    if recv_data:
                        Time = recv_data[:19]
                        Time = Time.decode('utf-8')
                        user_name = recv_data[19:27]  # 前8个字符
                        user_name = user_name.rstrip(b'?')
                        # user_name = user_name.strip('\0')  # 解码并去掉填充的 '\0'
                        user_name = user_name.decode('utf-8')
                        recv_text = recv_data[27:]
                        recv_text = recv_text.decode('utf-8')
                        print(recv_text)
                        # 主动给前端发送信息，使用 emit 来发送自定义事件
                        # api.send_text({"message": recv_text})
                        api.recv_text(Time, user_name, recv_text)
                        print("receive message:", recv_text)
                except ConnectionAbortedError as e:
                    pass
        print("close recv text thread stage2")

    def receive_audio(self):
        try:
            close = False
            BUFF_SIZE = 65536
            socket_audio = self.sockets['audio']
            streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
            print("[Info]: Starting audio playback monitoring...")
            while self.on_meeting and not close:
                if not self.sockets['audio']:
                    time.sleep(0.5)
                    continue
                try:
                    recv_data, addr = socket_audio.recvfrom(BUFF_SIZE)
                    if b'QUIT' in recv_data:
                        close = True
                        print("close recv audio thread stage 1")
                        continue
                    streamout.write(recv_data)
                except ConnectionAbortedError as e:
                    print(f"[Error]: Connection aborted: {e}")
                    break
            print("close recv audio thread stage 2")
        except Exception as e:
            print(f"[Error]: An error occurred in receive_audio: {e}")


    def start_camera_thread(self, user):
        """为每个新用户启动一个线程"""
        # if user not in self.camera_threads:
        # 为新用户启动线程
        recv_camera_thread = threading.Thread(target=self.receive_camera, args=(user,))
        recv_camera_thread.daemon = True  # 设置为守护线程
        recv_camera_thread.start()
        self.recv_thread.append(recv_camera_thread)
        # 将新线程存储在字典中，方便管理
        self.camera_threads[user] = recv_camera_thread
        print(f"为用户 {user} 启动了一个线程")

    def receive_camera_main(self):
        try:
            close = False
            socket_camera = self.sockets['camera']
            print("[Info]: Starting main camera playback monitoring...")
            while self.on_meeting and not close:
                if not self.sockets['camera']:
                    time.sleep(0.5)
                    continue
                # print("waiting address")
                recv_data, addr = socket_camera.recvfrom(400000)
                if b'QUIT' in recv_data:
                    close = True
                    print("close recv camera thread 1")
                    continue

                user_name = recv_data[:8]  # 前8个字符
                user = user_name.decode('utf-8').strip('\0')  # 解码并去掉填充的 '\0'
                if user not in self.camera_last:
                    self.camera_last[user] = None
                    self.start_camera_thread(user)
            print("close recv camera thread 2")

        except Exception as e:
            print(f"[Error]: An error occurred in receive_camera: {e}")

    def receive_camera(self, default_user):
        try:
            close = False
            socket_audio = self.sockets['camera']
            print("[Info]: Starting aux camera playback monitoring...")
            while self.on_meeting and not close:
                if not self.sockets['camera']:
                    time.sleep(0.5)
                    continue
                recv_data, addr = socket_audio.recvfrom(400000)
                if b'QUIT' in recv_data:
                    close = True
                    print("close recv aux camera thread 1")
                    continue

                user_name = recv_data[:8]  # 前8个字符
                user = user_name.decode('utf-8').strip('\0')  # 解码并去掉填充的 '\0'
                if user == default_user:
                    camera_data = recv_data[8:]  # 后面的数据
                    self.camera_last[default_user] = camera_data
                    api.recv_camera(default_user, camera_data)
            print("close recv aux camera thread 2")
        except Exception as e:
            print(f"[Error]: An error occurred in receive_camera: {e}")

    # def receive_screen(self):
    #     try:
    #         socket_screen = self.sockets['screen']
    #         print("[Info]: Starting screen playback monitoring...")
    #         id = 0
    #         complete_data = b''
    #         close = False
    #         while self.on_meeting and not close:
    #             recv_data, addr = socket_screen.recvfrom(400000)
    #             if b'QUIT' in recv_data:
    #                 close = True
    #                 print("close recv screen thread 1")
    #                 continue
    #             if recv_data:
    #                 identifier = recv_data[:2]  # 前 2 字节是标识符
    #                 frame_counter = int.from_bytes(identifier, byteorder='big')
    #                 if id != frame_counter:
    #                     if complete_data:
    #                         # np_arr = np.frombuffer(complete_data, dtype=np.uint8)
    #                         # img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    #                         # img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    #                         api.recv_screen(complete_data)
    #                     id = frame_counter
    #                     complete_data = b''
    #                 chunk = recv_data[2:]
    #                 complete_data += chunk
    #     except Exception as e:
    #         print(f"[Error]: {e}")
    # def receive_screen(self):
    #     try:
    #         socket_screen = self.sockets['screen']
    #         print("[Info]: Starting screen playback monitoring...")
    #         id = 0
    #         complete_data = b''
    #         while self.on_meeting:
    #             # 接收数据
    #             recv_data, addr = socket_screen.recvfrom(400000)  # 假设最大UDP数据包大小为 400KB
    #             if recv_data:
    #                 identifier = recv_data[:2]  # 前 2 字节是标识符
    #                 frame_counter = int.from_bytes(identifier, byteorder='big')
    #                 if id != frame_counter:
    #                     if complete_data:
    #                         np_arr = np.frombuffer(complete_data, dtype=np.uint8)
    #                         img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    #                         if img is not None:
    #                             img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    #                             api.recv_screen(img_rgb)
    #                         else:
    #                             print(f"[Error]: Failed to decode image")
    #                     id = frame_counter
    #                     complete_data = b''
    #                 chunk = recv_data[2:]
    #                 complete_data += chunk
    #     except Exception as e:
    #         print(f"[Error]: {e}")
    def receive_screen(self):
        try:
            close = False
            socket_screen = self.sockets['screen']
            print("[Info]: Starting screen playback monitoring...")
            id = 0
            complete_data = b''
            while self.on_meeting and not close:
                recv_data, addr = socket_screen.recvfrom(400000)
                if b'QUIT' in recv_data:
                    close = True
                    print("close recv screen thread 1")
                    continue
                if recv_data:
                    identifier = recv_data[:2]  # 前 2 字节是标识符
                    frame_counter = int.from_bytes(identifier, byteorder='big')
                    if id != frame_counter:
                        if complete_data:
                            # # 解码图像数据并转换为RGB
                            # np_arr = np.frombuffer(complete_data, dtype=np.uint8)
                            # img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                            # img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            # # 将图像转换为 JPEG 格式的字节数据
                            # _, img_encoded = cv2.imencode('.jpg', img_rgb)
                            # # 将字节数据转换为 Base64 字符串
                            # img_base64 = base64.b64encode(img_encoded).decode('utf-8')
                            # 传递 Base64 编码后的图像
                            api.recv_screen(complete_data)
                        id = frame_counter
                        complete_data = b''
                    chunk = recv_data[2:]
                    complete_data += chunk
            print("close recv screen thread 2")
        except Exception as e:
            print(f"[Error in receive_screen]: {e}")


    def share_switch(self, data_type):
        """
        switch for sharing certain type of data (screen, camera, audio, etc.)
        """
        if data_type not in self.support_data_types:
            print(f"[Warn]: Data type {data_type} is not supported.")
            return
        if self.acting_data_types[data_type]:
            if data_type == "screen":
                command = "[COMMAND]: CLOSE SCREEN"
                self.established_client.sendall(command.encode('utf-8'))
            self.acting_data_types[data_type] = False
            print(f"[Info]: Closing sharing for {data_type}...")
        else:
            if data_type == "screen":
                command = "[COMMAND]: OPEN SCREEN"
                self.established_client.sendall(command.encode('utf-8'))
                print("request open screen...")
                # response = await self.send_request(f"[COMMAND]: OPEN SCREEN")
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
