import queue
import struct
from conf_opt import *
from util import *
from config import *
from log_register_func import *
import api
import threading

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
        self.acting_data_types['camera'] = True
        self.ports = {'audio': 8001, 'screen': 8002, 'camera': 8003, 'text': 8004}
        # 用来存不同类型的socket
        self.sockets = {}
        self.camera_queues = {}
        self.camera_last = {}
        self.text = None
        self.can_share_screen = True
        self.conference_info = None  # you may need to save and update some conference_info regularly
        self.established_client = None
        self.frame = None
        self.cap = None

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
        self.on_meeting = False
        self.conference_id = None
        # Close all active connections

    async def send_request(self, request_data):
        """
        Send a request to the main server and receive the response.
        """
        try:
            self.established_client.send(request_data.encode())
            response = server_response(self.established_client, None).decode("utf-8")
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
        print("good")

        cap = cv2.VideoCapture(0)
        self.cap = cap
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)

        self.send_info()
        print("pass1")
        self.recv_info()
        print("pass2")

        while True:
            if self.frame is not None:
                print("[Info]: Frame received...")
                cv2.imshow('camera', self.frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    def send_info(self):
        """Capture, compress, and send camera image to the server."""
        # send_text_thread = threading.Thread(target=self.send_texts)
        # send_text_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        # send_text_thread.start()
        #
        # send_audio_thread = threading.Thread(target=self.send_audio)
        # send_audio_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        # send_audio_thread.start()

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

        # recv_camera_thread = threading.Thread(target=self.receive_camera)
        # recv_camera_thread.daemon = True  # 设置为守护线程，程序退出时自动关闭
        # recv_camera_thread.start()

    def send_texts(self, fps_or_frequency):
        print("run send text")
        established_text = self.sockets['text']
        # while(True):
        while self.on_meeting:
            # print("[Info]: Sending text...")
            # # 等待事件触发
            # print("self.text:", self.text)
            # # 事件触发后处理数据
            if self.text:
                print("[Info]: Updating text...")
                print(f"[Info]: Sending: {self.text}")
                established_text.send(self.text.encode('utf-8'))
                self.text = None

    def send_audio(self):
        try:
            streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            established_audio = self.sockets['audio']
            print("run send audio")
            while self.on_meeting:
                try:
                    data = streamin.read(CHUNK)
                    if not data:
                        continue
                    try:
                        established_audio.sendall(data)
                    except socket.error as e:
                        print(f"[Error]: Socket error during audio send: {e}")
                except socket.error as e:
                    print(f"[Error]: Socket error during audio send: {e}")
                    # 处理连接错误，可以重新尝试连接或退出
                    break  # 连接中断，退出循环
                except Exception as e:
                    print(f"[Error]: Unexpected error during audio send: {e}")
                    break  # 捕获其他异常，退出循环
        except Exception as e:
            print(f"[Error]: Error in send_audio: {e}")

    def send_camera(self):
        while self.on_meeting:
            established_text = self.sockets['text']
            established_audio = self.sockets['audio']
            established_camera = self.sockets['camera']

            if self.acting_data_types['text']:
                if self.text:
                    print("[Info]: Updating text...")
                    print(f"[Info]: Sending: {self.text}")
                    established_text.send(self.text.encode('utf-8'))
                    self.text = None

            if self.acting_data_types['audio']:
                try:
                    data = streamin.read(CHUNK)
                    if not data:
                        continue
                    try:
                        established_audio.sendall(data)
                    except socket.error as e:
                        print(f"[Error]: Socket error during audio send: {e}")
                except socket.error as e:
                    print(f"[Error]: Socket error during audio send: {e}")
                    break
                except Exception as e:
                    print(f"[Error]: Unexpected error during audio send: {e}")
                    break

            if self.acting_data_types['camera']:
                # if self.acting_data_types['camera']:
                #     print("running send_camera")
                if not self.cap.isOpened():
                    cap = cv2.VideoCapture(0)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
                ret, frame = self.cap.read()  # 获取图像
                # # cv2.destroyAllWindows()
                # if frame is not None:
                #     print("yes")
                #     self.frame = frame
                # 不加await gather，可以运行
                try:
                    if ret:
                        message = b''
                        # cv2.imshow("Camera", frame)  # 显示图像
                        # cv2.waitKey(0)  # 按任意键关闭显示窗口
                        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        byte_io = BytesIO()
                        pil_image.save(byte_io, format='JPEG')  # 或者 'PNG'，根据需要选择格式
                        image_bytes = byte_io.getvalue()  # 获取字节流

                        # 自己image放入queue
                        image = decompress_image(image_bytes)

                        head_bytes = "head".encode('utf-8')  # len(head_byte) = 4
                        message += head_bytes

                        user_bytes = self.user_name.encode('utf-8')
                        message += user_bytes + b'\0' * (16 - len(user_bytes))  # 前16个字节

                        image_length_bytes = struct.pack('!I', len(image_bytes))
                        message += image_length_bytes

                        message += image_bytes

                        self.camera_queues[self.user_name].put_nowait(image)

                        print(len(self.camera_queues))
                        print(self.camera_queues.items())
                        print(self.camera_queues[self.user_name].qsize())

                        established_camera.sendall(message)

                        screen_image = None
                        camera_images = None
                        for user_id, queue in self.camera_queues.items():
                            if not queue.empty():
                                if user_id == self.user_name:
                                    print("[Info]: Updating camera image")
                                    screen_image = queue.get()
                                else:
                                    if camera_images is None:
                                        camera_images = []
                                    if queue is not None:
                                        image = queue.get()  # 异步获取图像字节流
                                        self.camera_last[user_id] = image
                                    else:
                                        image = self.camera_last[user_id]
                                        # width, height = image.size
                                        # image = Image.fromarray(np.zeros((height, width, 3), dtype=np.uint8))
                                    # pil_image = decompress_image(image_bytes)  # 解压字节流为 PIL.Image send_camera已经decompress
                                    camera_images.append(image)  # 将 PIL.Image 添加到 camera_images 列表

                        print(type(screen_image))
                        print(type(camera_images))
                        screen = overlay_camera_images(screen_image, camera_images)
                        print(type(screen))

                        if isinstance(screen, Image.Image):  # 确保 screen 是 PIL.Image 类型
                            print("[Info]: Updating camera image")
                            screen_image_np = np.array(screen)  # 转换为 numpy.ndarray
                            frame = cv2.cvtColor(screen_image_np, cv2.COLOR_RGB2BGR)
                            self.frame = frame
                            # cv2.imshow('camera', frame)
                        else:
                            print("[Error]: overlay_camera_images did not return a PIL.Image object.")
                except ConnectionAbortedError as e:
                    print(f"[Error]: Connection aborted: {e}")
        else:
            self.cap.release()

    def receive_text(self, decompress=None):
        established_text = self.sockets['text']
        # while self.on_meeting:
        if not established_text:
            print("[Info]: 初始化失败")
        print("[Info]: Starting text playback monitoring...")
        while self.on_meeting:
            recv_data = established_text.recv(1024)
            if recv_data:
                recv_data = recv_data.decode('utf-8')
                print("receive message:", recv_data)

    def receive_audio(self):
        try:
            established_audio = self.sockets['audio']
            streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
            print("Run into audio")
            while self.on_meeting:
                try:
                    # 接收音频数据
                    recv_data = established_audio.recv(1024)
                    streamout.write(recv_data)
                    print("Received audio data")
                except ConnectionAbortedError as e:
                    print(f"[Error]: Connection aborted: {e}")
                    break
        except Exception as e:
            print(f"[Error]: An error occurred in receive_audio: {e}")

    def receive_camera(self, decompress=None):
        print("[Info]: Starting camera playback monitoring...")
        # loop = asyncio.get_event_loop()
        established_camera = self.sockets['camera']
        # while self.on_meeting:
        if not established_camera:
            print("[info]: camera 初始化失败")
        # recv_data = None
        # recv_data = await loop.sock_recv(established_camera, 1024)
        head_bytes = b""
        while len(head_bytes) < 4:
            byte = established_camera.receive(1)
            if len(head_bytes) == 0 and byte == b"h":
                head_bytes += byte
            else:
                head_bytes = b""
            if len(head_bytes) == 1 and byte == b"e":
                head_bytes += byte
            else:
                head_bytes = b""
            if len(head_bytes) == 2 and byte == b"a":
                head_bytes += byte
            else:
                head_bytes = b""
            if len(head_bytes) == 3 and byte == b"d":
                head_bytes += byte
            else:
                head_bytes = b""

        user_bytes = established_camera.receive(16)
        user = user_bytes.decode('utf-8').strip('\0')  # 解码并去掉填充的 '\0'

        if user not in self.camera_queues:
            self.camera_queues[user] = queue.Queue()
            self.camera_last[user] = None

        image_length_bytes = established_camera.receive(4)
        image_length = struct.unpack('!I', image_length_bytes)[0]  # 解包得到图像的字节长度

        image_bytes = established_camera.receive(image_length)

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
