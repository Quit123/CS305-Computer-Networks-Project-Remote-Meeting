from flask import Flask, request, jsonify
import asyncio
import util
from log_register_func import *

app = Flask(__name__)
client_instance = app.config.get('CLIENT_INSTANCE')

# 用于存储登录状态
login_info = {
    "status": False
}
create = False
quit = False
cancel = False
join_info = {
    "con_id": None,
    "click": False
}


@app.route('/api/login', methods=['POST'])
def login():
    """Handle POST request for user login"""
    global allow_circle
    data = request.json
    username = data.get('username')
    password = data.get('password')
    use_input = f"{username}:{password}"
    recv = server_message_encrypt(use_input)
    if "Login successfully" in recv:
        login_info["status"] = True
        return jsonify({'status': 'success', 'message': 'Login successful'})
    else:
        login_info["status"] = False
        return jsonify({'status': 'fail', 'message': 'Login failed'})


@app.route('/api/create', methods=['POST'])
def Create():
    """Handle POST request for user login"""
    global create
    create = True
    # if username in users and users[username] == password:
    return jsonify({'status': 'success', 'message': 'Click login return'})


@app.route('/api/quit', methods=['POST'])
def Quit():
    """Handle POST request for user login"""
    global quit
    quit = True
    # if username in users and users[username] == password:
    return jsonify({'status': 'success', 'message': 'Click quit return'})


@app.route('/api/cancel', methods=['POST'])
def Cancel():
    """Handle POST request for user login"""
    global cancel
    cancel = True
    # if username in users and users[username] == password:
    return jsonify({'status': 'success', 'message': 'Click cancel return'})


@app.route('/api/join', methods=['POST'])
def Join():
    """Handle POST request for user login"""
    con_id = request.json
    join_info["con_id"] = con_id
    join_info["click"] = True
    # if username in users and users[username] == password:
    return jsonify({'status': 'success', 'message': 'Click join successful'})


@app.route('/update-audio-status', methods=['POST'])
def update_audio_status():
    """前端通过 POST 请求更新 text 状态"""
    client_instance.share_switch('audio')
    return jsonify({'status': 'success', 'audio_status': client_instance.acting_data_types['audio']})


@app.route('/update-camera-status', methods=['POST'])
def update_camera_status():
    """前端通过 POST 请求更新 camera 状态"""
    client_instance.share_switch('camera')
    return jsonify({'status': 'success', 'camera_status': client_instance.acting_data_types['camera']})


@app.route('/send-text', methods=['POST'])
def send_text():
    """前端通过 POST 请求发送文本消息"""
    data = request.json
    if 'message' in data:
        client_instance.text = data['message']
        client_instance.text_event.set()
        return jsonify({'status': 'success', 'message': client_instance.text})
    return jsonify({'status': 'error', 'message': 'Invalid data'}), 400


@app.route('/box-size', methods=['POST'])
def update_screen_size():
    """接收前端传入的边界框大小"""
    # global current_box_size
    data = request.json
    if 'width' in data and 'height' in data:
        util.current_screen_size = data
        print(f"接收到边界框大小：宽: {data['width']}，高: {data['height']}")
        return jsonify({'status': 'success', 'box_size': util.current_screen_size})
    return jsonify({'status': 'error', 'message': '无效的数据'}), 400
