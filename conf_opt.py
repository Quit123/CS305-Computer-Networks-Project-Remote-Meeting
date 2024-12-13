import asyncio
import aiohttp
import base64
import requests
import json
import socket
from util import *
from aiortc import VideoStreamTrack, RTCPeerConnection
from aiortc.contrib.media import MediaPlayer, MediaRelay
from api import app
from log_register_func import *
from flask_socketio import SocketIO, emit
import struct

client_instance = app.config.get('CLIENT_INSTANCE')


async def establish_connect(self):
    try:
        for type in self.support_data_types:
            port = self.ports.get(type)
            print("port:", port)
            if type == 'text':
                #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                established_client, info = connection_establish((self.server_addr[0], port))
                print("建立status：", info)
                self.sockets[type] = established_client
            if type == 'audio':
                # 尝试UDP
                # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 使用 UDP 协议
                # self.sockets[type] = sock
                # TCP
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.server_addr[0], port))
                self.sockets[type] = sock
            if type == 'camera':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.server_addr[0], port))
                self.sockets[type] = sock
        print(f"[Info]: Connected to '{self.server_addr[0]}' server.")
    except Exception as e:
        print(f"[Error]: Could not connect to '{self.server_addr[0]}' server: {e}")


async def close_connection(self):
    """
        Close the persistent connection to the server.
        """
    for reader, writer in self.sockets:
        reader.close()
        writer.close()
    print("[Info]: Connection closed with the server.")


async def send_camera_frame_to_frontend(camera_images):
    """
    Send camera frame to the frontend via API
    """
    try:
        url = 'http://localhost:5000/api/receive_camera_frame'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=camera_images) as response:
                if response.status == 200:
                    print("Frame successfully sent to frontend.")
                else:
                    print(f"Error: {response.status}")
    except Exception as e:
        print(f"Failed to send camera frame to frontend: {e}")


async def output_data(self, fps_or_frequency):
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
        await send_camera_frame_to_frontend(all_user_camera_data)
    if not self.data_queues['text'].empty():
        received_message = self.text_queue.get()
        try:
            with open('user_commands.txt', 'a', encoding='utf-8') as f:
                f.write(received_message)
        except Exception as e:
            print(f"upload entry error: {e}")

    await asyncio.sleep(1 / fps_or_frequency)


# async def send_datas(self):
#     # await asyncio.gather(send_texts(self), send_audio(self), send_camera(self))
#     await asyncio.gather(send_texts(self))
#
#     await asyncio.sleep(0)


async def send_texts(self, fps_or_frequency):
    print("run send text")
    while(True):
        established_text = self.sockets['text']
        # print("[Info]: Sending text...")
        # # 等待事件触发
        # print("self.text:", self.text)
        # # 事件触发后处理数据
        if self.text:
            print("[Info]: Updating text...")
            print(f"[Info]: Sending: {self.text}")
            established_text.send(self.text.encode('utf-8'))
            self.text = None
            # self.text_event.clear()  # 重置事件
        await asyncio.sleep(1/fps_or_frequency)


async def receive_text(self, decompress=None):
    loop = asyncio.get_event_loop()
    established_text = self.sockets['text']
    while self.on_meeting:
        if not established_text:
            print("[Info]: 初始化失败")
        recv_data = None
        print("[Info]: Starting text playback monitoring...")
        # recv_data = established_text.recv(1024)
        recv_data = await loop.sock_recv(established_text, 1024)
        # while self.on_meeting:
        # recv_data = await asyncio.wait_for(established_text.recv(1024), timeout=1/30)
        if(recv_data):
            print("receive message:", recv_data)
            recv_data = recv_data.decode('utf-8')
        await asyncio.sleep(1)


# 发送音频数据的线程
async def send_audio(self, fps_or_frequency):
    try:
        streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("run send audio")
        while self.on_meeting:
            try:
                data = streamin.read(CHUNK)  # 从麦克风读取音频数据
                if not data:
                    print("[Warning]: No audio data received.")
                    continue  # 没有数据时跳过，避免发送空数据

                self.sockets['audio'].sendall(data)  # 通过 socket 发送数据

            except socket.error as e:
                print(f"[Error]: Socket error during audio send: {e}")
                # 处理连接错误，可以重新尝试连接或退出
                break  # 连接中断，退出循环
            except Exception as e:
                print(f"[Error]: Unexpected error during audio send: {e}")
                break  # 捕获其他异常，退出循环
            await asyncio.sleep(1 / (fps_or_frequency * 3))
    except Exception as e:
        print(f"[Error]: Error in send_audio: {e}")


# 接收音频数据并播放的线程
async def receive_audio(self, fps_or_frequency):
    try:
        loop = asyncio.get_event_loop()
        established_text = self.sockets['audio']
        streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        print("run into audio")

        while self.on_meeting:
            try:
                recv_data = await loop.sock_recv(established_text, 1024)
                # if isinstance(recv_data, bytes):  # 确保数据是字节类型
                #     streamout.write(recv_data)
                streamout.write(recv_data)

                if not self.acting_data_types['audio']:
                    print("[Warning]: Connection closed by server")
                    break  # 连接被关闭，退出循环

                print("Received audio data")
                # 处理数据...
            except ConnectionAbortedError as e:
                print(f"[Error]: Connection aborted: {e}")
                break
            # await asyncio.sleep(1/fps_or_frequency)
    except Exception as e:
        print(f"[Error]: An error occurred in receive_audio: {e}")
        # print("receive audio")
        # recv_data = await loop.sock_recv(established_text, 1024)
        # # data = self.sockets['audio'].recv(CHUNK)     # 从服务器接收音频数据
        # streamout.write(recv_data)       # 播放音频数据到扬声器
        # await asyncio.sleep(1 / fps_or_frequency)

# async def send_audio(self):
#     while self.is_working and self.on_meeting:
#         if not self.acting_data_types['audio']:
#             await asyncio.sleep(0.2)
#             continue
#         if not streamin.is_active():
#             streamin.start_stream()
#         reader, writer = self.sockets['audio']
#         while self.is_working and self.on_meeting and self.acting_data_types['audio']:
#             audio_chunk = streamin.read(CHUNK)
#             if not audio_chunk:
#                 break
#             writer.write(audio_chunk)
#             await writer.drain()
#         streamin.stop_stream()
#
#
# async def receive_audio(self, decompress=None):
#     """
#         running task: keep receiving certain type of data (save or output)
#         you can create other functions for receiving various kinds of data
#         """
#     print("[Info]: Starting audio playback monitoring...")
#     reader, writer = self.sockets['audio']
#     while self.on_meeting:
#         # 挂起
#         audio_chunk = await reader.read(CHUNK)
#         self.data_queues['audio'].put_nowait(audio_chunk)

    # sock = self.sockets['camera']
    # while self.is_working and self.on_meeting:
    #     if not self.acting_data_types['camera']:
    #         await asyncio.sleep(0)
    #         continue
    #     try:
    #         # Capture image from the camera
    #         camera_image = await capture_camera()
    #         # Compress the image
    #         compressed_image = await compress_image(camera_image)
    #         # User's name (assuming you have a 'user_name' attribute in the class)
    #         user_name = self.user_name  # Replace with your actual user name attribute
    #         # Create a message to send: a dictionary with user name and the compressed image
    #         message = {
    #             'user_name': user_name,
    #             'Length': len(compressed_image),
    #             'image': compressed_image
    #         }
    #         message_bytes = json.dumps(message).encode('utf-8')  # Convert to JSON byte stream
    #         await asyncio.get_event_loop().sock_sendall(sock, message_bytes)
    #     except Exception as e:
    #         print(f"Error sending camera image: {e}")
    #     await asyncio.sleep(0)

# # open
# cap = cv2.VideoCapture(0)
# if cap.isOpened():
#     can_capture_camera = True
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
# else:
#     can_capture_camera = False
# # close
# cap.release()

async def send_camera(self, fps_or_frequency):
    """Capture, compress, and send camera image to the server."""
    cap = cv2.VideoCapture(0)
    while self.on_meeting:
        if self.acting_data_types['camera']:
            if not cap.isOpened():
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
            try:
                await asyncio.sleep(1 / fps_or_frequency * 3)

                camera_images = []
                screen_image = None
                for user_id, queue in self.data_queues.items():
                    if not queue.empty():
                        if user_id == self.user_name:
                            screen_image = queue.get()
                        image_bytes = await queue.get()  # 异步获取图像字节流
                        pil_image = decompress_image(image_bytes)  # 解压字节流为 PIL.Image
                        camera_images.append(pil_image)  # 将 PIL.Image 添加到 camera_images 列表
                screen = overlay_camera_images(screen_image, camera_images)
                # 假设 screen_image 是 PIL.Image 类型
                screen_image_np = np.array(screen)  # 将 PIL.Image 转换为 numpy.ndarray
                # 如果需要，将其从 RGB 转换为 BGR（因为 OpenCV 使用 BGR）
                frame = cv2.cvtColor(screen_image_np, cv2.COLOR_RGB2BGR)  # 转换为 BGR 格式以便 OpenCV 使用
                cv2.imshow('camera', frame)

                ret, frame = cap.read()  # 获取图像
                if ret:
                    message = None
                    # cv2.imshow("Camera", frame)  # 显示图像
                    # cv2.waitKey(0)  # 按任意键关闭显示窗口
                    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    byte_io = BytesIO()
                    pil_image.save(byte_io, format='JPEG')  # 或者 'PNG'，根据需要选择格式
                    image_bytes = byte_io.getvalue()  # 获取字节流

                    # 自己image放入queue
                    image = decompress_image(image_bytes)
                    self.data_queues[self.user_name].put(image)

                    head_bytes = "head".encode('utf-8')  # len(head_byte) = 4
                    message += head_bytes

                    user_bytes = self.user_name.encode('utf-8')
                    message += user_bytes + b'\0' * (16 - len(user_bytes))  # 前16个字节

                    image_length_bytes = struct.pack('!I', len(image_bytes))
                    message += image_length_bytes

                    message += image_bytes

                    self.sockets['camera'].sendall(image_bytes)
            except ConnectionAbortedError as e:
                print(f"[Error]: Connection aborted: {e}")
        else:
            cap.release()


    # cap = cv2.VideoCapture(0)
    # # 创建 RTP 连接
    # pc = RTCPeerConnection()
    # relay = MediaRelay()
    # # 创建 CameraStreamTrack 实例
    # track = CameraStreamTrack(cap)
    # pc.addTrack(track)
    # # 进行 WebRTC 信令交换，生成 offer 和设置本地描述
    # offer = await pc.createOffer()
    # offer.sdp = add_user_name_to_sdp(offer.sdp, self.user_name)
    # await pc.setLocalDescription(offer)
    # # 在实际应用中，需要通过信令交换将 offer 发给远程端，获取远程端的 answer
    # print("Offer created and local description set. Now awaiting connection...")
    # # 维持连接，持续发送视频
    # await asyncio.sleep(3600)  # 1小时后关闭连接
    # # 清理工作
    # await pc.close()
    # cap.release()


async def receive_camera(self, decompress=None):
    print("[Info]: Starting camera playback monitoring...")
    loop = asyncio.get_event_loop()
    established_camera = self.sockets['camera']
    while self.on_meeting:
        if not established_camera:
            print("[info]: camera 初始化失败")
        # recv_data = None
        # recv_data = await loop.sock_recv(established_camera, 1024)
        head_bytes = b""
        while len(head_bytes) < 4:
            byte = await loop.sock_recv(established_camera, 1)
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

        user_bytes = await loop.sock_recv(established_camera, 16)
        user = user_bytes.decode('utf-8').strip('\0')  # 解码并去掉填充的 '\0'

        if user not in self.camera_queues:
            self.data_queues[user] = asyncio.Queue()

        image_length_bytes = await loop.sock_recv(established_camera, 4)
        image_length = struct.unpack('!I', image_length_bytes)[0]  # 解包得到图像的字节长度

        image_bytes = await loop.sock_recv(established_camera, image_length)

        image = decompress_image(image_bytes)
        self.data_queues[user].put(image)


async def ask_new_clients_and_share_screen(self):
    """向服务器询问是否有新客户端加入会议"""
    try:
        while self.is_working and self.on_meeting:
            await asyncio.sleep(1)
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

    async def recv(self):
        if client_instance.acting_data_types['camera']:
            ret, frame = self.cap.read()  # 获取视频帧
            if not ret:
                raise Exception("Cannot read frame")
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_bytes = self.compress_image(pil_image)
            await asyncio.sleep(1 / 30)
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
