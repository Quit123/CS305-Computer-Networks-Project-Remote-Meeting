'''
Simple util implementation for video conference
Including data capture, image compression and image overlap
Note that you can use your own implementation as well :)
'''
from io import BytesIO
import pyaudio
import cv2
import pyautogui
import numpy as np
from PIL import Image, ImageGrab
from config import *
from aiortc import VideoStreamTrack, RTCPeerConnection

# audio setting
FORMAT = pyaudio.paInt16
audio = pyaudio.PyAudio()

from flask import Flask
from flask_socketio import SocketIO, emit
import wave
import pyaudio

app = Flask(__name__)
socketio = SocketIO(app)

streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# print warning if no available camera
cap = cv2.VideoCapture(0)
if cap.isOpened():
    can_capture_camera = True
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
else:
    can_capture_camera = False


current_screen_size = {'width': 0, 'height': 0}
# my_screen_size = pyautogui.size()

screen_image = Image.new('RGB', (current_screen_size['width'], current_screen_size['height']), color=(0, 0, 0))


def add_user_name_to_sdp(offer_sdp, user_name):
    # 修改原始 SDP 来添加用户名信息（示例：在 origin 字段后附加用户名）
    modified_sdp = offer_sdp + f"\n# User Name: {user_name}"
    return modified_sdp


def parse_client_id_from_offer(offer_sdp):
    # 查找包含用户名的行
    user_name_line = None
    for line in offer_sdp.splitlines():
        if line.startswith("# User Name:"):
            user_name_line = line
            break
    if user_name_line:
        # 提取用户名
        user_name = user_name_line[len("# User Name: "):].strip()
        # 移除用户名行，恢复原始的 SDP 内容
        original_sdp = "\n".join(line for line in offer_sdp.splitlines() if not line.startswith("# User Name:"))
        return user_name, original_sdp
    else:
        return None, offer_sdp  # 如果没有找到用户名，返回原始的 SDP


def resize_image_to_fit_screen(image, my_screen_size):
    screen_width, screen_height = my_screen_size['width'], my_screen_size['height']

    original_width, original_height = image.size

    aspect_ratio = original_width / original_height

    if screen_width / screen_height > aspect_ratio:
        # resize according to height
        new_height = screen_height
        new_width = int(new_height * aspect_ratio)
    else:
        # resize according to width
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)

    # resize the image
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    return resized_image


def overlay_camera_images(screen_image, camera_images):
    """
    screen_image: PIL.Image
    camera_images: list[PIL.Image]
    """
    if screen_image is None and camera_images is None:
        print('[Warn]: cannot display when screen and camera are both None')
        return None
    if screen_image is not None:
        screen_image = resize_image_to_fit_screen(screen_image, current_screen_size)

    if camera_images is not None:
        # make sure same camera images
        if not all(img.size == camera_images[0].size for img in camera_images):
            raise ValueError("All camera images must have the same size")

        screen_width, screen_height = (
            current_screen_size['width'], current_screen_size['height']) if screen_image is None else screen_image.size
        camera_width, camera_height = camera_images[0].size

        # calculate num_cameras_per_row
        num_cameras_per_row = screen_width // camera_width

        # adjust camera_imgs
        if len(camera_images) > num_cameras_per_row:
            adjusted_camera_width = screen_width // len(camera_images)
            adjusted_camera_height = (adjusted_camera_width * camera_height) // camera_width
            camera_images = [img.resize((adjusted_camera_width, adjusted_camera_height), Image.LANCZOS) for img in
                             camera_images]
            camera_width, camera_height = adjusted_camera_width, adjusted_camera_height
            num_cameras_per_row = len(camera_images)

        # if no screen_img, create a container
        if screen_image is None:
            display_image = Image.fromarray(np.zeros((camera_width, current_screen_size['height'], 3), dtype=np.uint8))
        else:
            display_image = screen_image
        # cover screen_img using camera_images
        for i, camera_image in enumerate(camera_images):
            row = i // num_cameras_per_row
            col = i % num_cameras_per_row
            x = col * camera_width
            y = row * camera_height
            display_image.paste(camera_image, (x, y))

        return display_image
    else:
        return screen_image


def capture_screen():
    # capture screen with the resolution of display
    # img = pyautogui.screenshot()
    img = ImageGrab.grab()
    return img


# def capture_camera():
#     # capture frame of camera
#     ret, frame = cap.read()
#     if not ret:
#         raise Exception('Fail to capture frame from camera')
#     return Image.fromarray(frame)


# def capture_voice():
#     return streamin.read(CHUNK)


def decompress_image(image_bytes):
    """
    decompress bytes to PIL.Image
    :param image_bytes: bytes, compressed data
    :return: PIL.Image
    """
    img_byte_arr = BytesIO(image_bytes)
    image = Image.open(img_byte_arr)

    return image
