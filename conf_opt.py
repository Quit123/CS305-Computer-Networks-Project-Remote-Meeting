import asyncio
import aiohttp
import base64
from util import *
from aiortc import VideoStreamTrack, RTCPeerConnection
from api import app
from log_register_func import *


client_instance = app.config.get('CLIENT_INSTANCE')


def establish_connect(self):
    try:
        for type in self.support_data_types:
            port = self.ports.get(type)
            print("port:", port)
            if type == 'text':
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('0.0.0.0', port))  # 绑定到本地地址和端口
                #established_client, info = connection_establish((self.server_addr[0], port))
                self.sockets[type] = sock
            if type == 'audio':
                # 尝试UDP
                BUFF_SIZE = 65536
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 使用 UDP 协议
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
                sock.bind(('0.0.0.0', port))  # 绑定到本地地址和端口
                self.sockets[type] = sock
                # TCP
                # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # sock.connect((self.server_addr[0], port))
                # self.sockets[type] = sock
            if type == 'camera':
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('0.0.0.0', port))
                self.sockets[type] = sock
                # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # sock.connect((self.server_addr[0], port))
                # self.sockets[type] = sock
        print(f"[Info]: Connected to '{self.server_addr[0]}' server.")
    except Exception as e:
        print(f"[Error]: Could not connect to '{self.server_addr[0]}' server: {e}")


def close_connection(self):
    """
        Close the persistent connection to the server.
        """
    for reader, writer in self.sockets:
        reader.close()
        writer.close()
    print("[Info]: Connection closed with the server.")


def send_camera_frame_to_frontend(camera_images):
    """
    Send camera frame to the frontend via API
    """
    try:
        url = 'http://localhost:5000/api/receive_camera_frame'
        with aiohttp.ClientSession() as session:
            with session.post(url, json=camera_images) as response:
                if response.status == 200:
                    print("Frame successfully sent to frontend.")
                else:
                    print(f"Error: {response.status}")
    except Exception as e:
        print(f"Failed to send camera frame to frontend: {e}")


def output_data(self, fps_or_frequency):
    """
        running task: output received stream data
        """
    screen_image = None
    if not self.data_queues['screen'].empty():
        screen_image = decompress_image(self.data_queues['screen'].get())
        screen_image.show()
    if not self.data_queues['camera'].empty():
        all_user_camera_data = []
        for username, user_camera_queue in self.data_queues['camera'].items():
            if not user_camera_queue.empty():
                # 获取摄像头图像并解压
                camera_image_bytes = user_camera_queue.get()
                camera_image = decompress_image(camera_image_bytes)
                all_user_camera_data.append({
                    'username': username,
                    'camera_image': base64.b64encode(camera_image).decode('utf-8')
                })
        send_camera_frame_to_frontend(all_user_camera_data)
    if not self.data_queues['text'].empty():
        received_message = self.text_queue.get()
        try:
            with open('user_commands.txt', 'a', encoding='utf-8') as f:
                f.write(received_message)
        except Exception as e:
            print(f"upload entry error: {e}")


def ask_new_clients_and_share_screen(self):
    """向服务器询问是否有新客户端加入会议"""
    try:
        while self.on_meeting:
            num = len(self.data_queues['audio'])
            inquire = f"[ASK]: New client connect ?\n[STATUS]: {num} \n[ASK]: Can I sharing ?"
            check = self.send_request(inquire)
            if "No" in check:
                print("[Info]: No new clients.")
            else:
                name = check.split(":")[1].strip().split()[1]
                if name not in self.data_queues['audio']:
                    self.data_queues['audio'][name] = asyncio.Queue()
                    print("[Info]: New clients have joined the meeting.")
                    self.send_request("[ACK]: Has prepared")
            if "True" in check:
                self.can_share_screen = True
            else:
                self.can_share_screen = False
    except Exception as e:
        print(f"[Error]: Error while querying server for new clients - {e}")


class CameraStreamTrack(VideoStreamTrack):
    def __init__(self, cap):
        super().__init__()  # 初始化父类
        self.cap = cap  # OpenCV 捕获设备
        if not self.cap.isOpened():
            raise Exception("Cannot open camera")
        else:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)

    def recv(self):
        if client_instance.acting_data_types['camera']:
            ret, frame = self.cap.read()  # 获取视频帧
            if not ret:
                raise Exception("Cannot read frame")
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_bytes = self.compress_image(pil_image)
            return frame_bytes

    @staticmethod
    def compress_image(image, format='JPEG', quality=85):
        """
            compress image and output Bytes

            :param image: PIL.Image, input image
            :param format: str, output format ('JPEG', 'PNG', 'WEBP', ...)
            :param quality: int, compress quality (0-100), 85 default
            :return: bytes, compressed image data
            """
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=format, quality=quality)
        img_byte_arr = img_byte_arr.getvalue()
        return img_byte_arr
