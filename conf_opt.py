import asyncio
import aiohttp
import base64
import requests
import json
import socket
from util import *
from aiortc import VideoStreamTrack, RTCPeerConnection
from aiortc.contrib.media import MediaPlayer, MediaRelay


async def establish_connect(self):
    try:
        for type in self.support_data_types:
            port = self.ports.get(type)
            if type == 'camera':
                self.sockets[type] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # 设置为 非阻塞模式
                self.sockets[type].setblocking(False)
                # 为什么要await？
                await asyncio.get_event_loop().sock_connect(self.sock, (self.server_addr[0], port))
            else:
                reader, writer = await asyncio.open_connection(self.server_addr[0], port)
                self.sockets[type] = (reader, writer)
        print(f"[Info]: Connected to '{self.server_addr}' server.")
    except Exception as e:
        print(f"[Error]: Could not connect to '{self.server_addr}' server: {e}")


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
    while self.on_meeting:
        # Example for outputting received data (can be extended to handle all data types)
        if not self.data_queues['audio'].empty():
            if not streamout.is_active():
                streamout.start_stream()
            streamout.write(self.data_queues['audio'].get())
        else:
            streamout.stop_stream()
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


async def send_datas(self):
    await asyncio.gather(send_texts(self), send_audio(self), send_camera(self))

    # if self.acting_data_types['video']:
    #     pass
    # if self.acting_data_types['audio']:
    #     pass
    await asyncio.sleep(0)


async def send_texts(self):
    while self.is_working and self.on_meeting:
        print("[Info]: Starting text transmission...")
        reader, writer = self.sockets['text']
        while self.is_working and self.on_meeting:
            # 等待事件触发
            await self.text_event.wait()
            # 事件触发后处理数据
            if self.text:
                print(f"[Info]: Sending: {self.text}")
                writer.write(self.text.encode())
                await writer.drain()
                self.text_event.clear()  # 重置事件


async def receive_text(self, decompress=None):
    print("[Info]: Starting text playback monitoring...")
    reader, writer = self.sockets['text']
    while self.on_meeting:
        text_chunk = await reader.read(CHUNK)
        self.data_queues['text'].put_nowait(text_chunk)


async def send_audio(self):
    while self.is_working and self.on_meeting:
        if not self.acting_data_types['audio']:
            await asyncio.sleep(0.2)
            continue
        if not streamin.is_active():
            streamin.start_stream()
        reader, writer = self.sockets['audio']
        while self.is_working and self.on_meeting and self.acting_data_types['audio']:
            audio_chunk = streamin.read(CHUNK)
            if not audio_chunk:
                break
            writer.write(audio_chunk)
            await writer.drain()
        streamin.stop_stream()


async def receive_audio(self, decompress=None):
    """
        running task: keep receiving certain type of data (save or output)
        you can create other functions for receiving various kinds of data
        """
    print("[Info]: Starting audio playback monitoring...")
    reader, writer = self.sockets['audio']
    while self.on_meeting:
        # 挂起
        audio_chunk = await reader.read(CHUNK)
        self.data_queues['audio'].put_nowait(audio_chunk)

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


async def send_camera(self):
    """Capture, compress, and send camera image to the server."""
    cap = cv2.VideoCapture(0)
    # 创建 RTP 连接
    pc = RTCPeerConnection()
    relay = MediaRelay()
    # 创建 CameraStreamTrack 实例
    track = CameraStreamTrack(cap)
    pc.addTrack(track)
    # 进行 WebRTC 信令交换，生成 offer 和设置本地描述
    offer = await pc.createOffer()
    offer.sdp = add_user_name_to_sdp(offer.sdp, self.user_name)
    await pc.setLocalDescription(offer)
    # 在实际应用中，需要通过信令交换将 offer 发给远程端，获取远程端的 answer
    print("Offer created and local description set. Now awaiting connection...")
    # 维持连接，持续发送视频
    await asyncio.sleep(3600)  # 1小时后关闭连接
    # 清理工作
    await pc.close()
    cap.release()


async def receive_camera(self, decompress=None):
    print("[Info]: Starting camera playback monitoring...")
    sock = self.sockets['camera']
    while self.on_meeting:
        data, _ = await asyncio.get_event_loop().sock_recv(sock, 1500)  # 1500 是 RTP 包的最大大小
        decoded_data = data.decode('utf-8')  # 解码为字符串
        message = json.loads(decoded_data)  # 将 JSON 字符串转换回字典
        user_name = message['user_name']  # 获取用户名
        compressed_image = message['image']  # 获取图像数据
        self.data_queues['camera'][user_name].put_nowait(compressed_image)


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
