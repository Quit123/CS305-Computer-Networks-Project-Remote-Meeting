import time

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send
import util
from log_register_func import *
from flask_cors import CORS
import datetime
import threading
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# 用于存储登录状态
login_info = {
    "status": False
}
create = False
quit = False
cancel = False
join_id = None
join_info = {
    "con_id": None,
    "click": False
}


# 具体功能之后完善

def keep_prog():
    print("keep running")
    time.sleep(60)


@app.route('/api/login', methods=['POST'])
def login():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    print("click login")
    data = request.json
    username = data.get('username')
    password = data.get('password')
    use_input = f"login {username} {password}"
    print("client_instance:", client_instance)
    print("use_input:", use_input)
    recv = server_message_encrypt(use_input, client_instance)
    if "Login successfully" in recv:

        recv_change_info = threading.Thread(target=keep_prog)
        recv_change_info.daemon = True  # 设置为守护线程，程序退出时自动关闭
        recv_change_info.start()

        login_info["status"] = True
        client_instance.user_name = username
        # client_instance.camera_queues[username] = queue.Queue()
        client_instance.camera_last[username] = None
        return jsonify({'status': 'success', 'message': 'Login successful'})
    else:
        login_info["status"] = False
        return jsonify({'status': 'fail', 'message': 'Login failed'})


@app.route('/api/register', methods=['POST'])
def register():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    print("click register")
    data = request.json
    username = data.get('username')
    password = data.get('password')
    use_input = f"register {username} {password}"
    recv = server_message_encrypt(use_input, client_instance)
    if "Registering successfully" in recv:
        return jsonify({'status': 'success', 'message': 'Login successful'})
    else:
        return jsonify({'status': 'fail', 'message': 'Login failed'})


@app.route('/api/create', methods=['POST'])
def Create():
    print("click Create")
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    # global create
    # create = True
    client_instance.conference_type = 1
    client_instance.multi_initiator = True
    client_instance.host = True
    data = request.json
    title = data.get('title')
    title = title + " " + client_instance.user_name
    ans, con_id = client_instance.create_conference(title, client_instance.conference_type)
    # error = 0
    # if "Error" in ans:
    #     error = 1
    # print("pass")
    if "Success" in ans:
        print(jsonify({'status': 'success', 'message': con_id}))
        return jsonify({'status': 'success', 'message': con_id})
    else:
        return jsonify({'status': 'fail', 'message': ans})


# add new
@app.route('/api/create_P2P', methods=['POST'])
def Create_P2P():
    print("click Create")
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    client_instance.conference_type = 2
    client_instance.p2p_initiator = True
    data = request.json
    title = data.get('title')
    title = title + " " + client_instance.user_name
    ans, con_id = client_instance.create_conference(title, client_instance.conference_type)
    error = 0
    if "Error" in ans:
        error = 1
    print("pass")
    if error == 0:
        print(jsonify({'status': 'success', 'message': con_id}))
        return jsonify({'status': 'success', 'message': con_id})
    else:
        return jsonify({'status': 'fail', 'message': ans})


@app.route('/api/join', methods=['POST'])
def Join():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    con_in = request.json
    con_id = con_in.get('con_id')
    print("join conference:", con_id)
    con_id = con_id + " " + client_instance.user_name
    result = client_instance.join_conference(con_id)
    if 'Success' in result:
        return jsonify({'status': 'success', 'message': result})
    else:
        return jsonify({'status': 'fail', 'message': result})


# add new
@app.route('/api/check_list', methods=['POST'])
def Check_list():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    request_data = f"[COMMAND]: CHECK"
    response = client_instance.send_request(request_data)
    # user_name id user_name id
    if "Error" in response:
        return jsonify({'status': 'fail', 'message': response})
    else:
        print(jsonify({'status': 'success', 'message': response}))
        return jsonify({'status': 'success', 'message': response})


@app.route('/api/quit', methods=['POST'])
def Quit():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    # global quit
    # quit = True
    client_instance.quit_conference()
    # if username in users and users[username] == password:
    return jsonify({'status': 'success', 'message': 'Click quit return'})


@app.route('/api/cancel', methods=['POST'])
def Cancel():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    # global cancel
    # cancel = True
    # if client_instance.host:
    client_instance.cancel_conference()
    # if username in users and users[username] == password:
    time.sleep(1)
    if client_instance.allow_quit:
        return jsonify({'status': 'success', 'message': 'Click cancel return'})
    else:
        return jsonify({'status': 'fail', 'message': 'Click cancel return'})


@app.route('/api/update-audio-status', methods=['POST'])
def update_audio_status():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """前端通过 POST 请求更新 text 状态"""
    client_instance.share_switch('audio')
    return jsonify({'status': 'success', 'audio_status': client_instance.acting_data_types['audio']})


@app.route('/api/update-camera-status', methods=['POST'])
def update_camera_status():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """前端通过 POST 请求更新 camera 状态"""
    client_instance.share_switch('camera')
    return jsonify({'status': 'success', 'camera_status': client_instance.acting_data_types['camera']})


@app.route('/api/update-screen-status', methods=['POST'])
def update_screen_status():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """前端通过 POST 请求更新 camera 状态"""
    client_instance.share_switch('screen')
    return jsonify({'status': 'success', 'camera_status': client_instance.acting_data_types['screen']})
    # if "SUCCESS" in response:
    #     return jsonify({'status': 'success', 'camera_status': client_instance.acting_data_types['screen']})
    # else:
    #     return jsonify({'status': 'fail', 'camera_status': response})


@socketio.on('message')
def send_text(msg):
    # 自己发送的信息要传用户名
    # server发送的信息需要特殊标识一下
    # print(str(msg))
    client_instance = app.config.get('CLIENT_INSTANCE')
    json_message = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": client_instance.user_name,
        "message": msg['message']
    }
    send(json_message)
    """前端通过 POST 请求发送文本消息"""
    client_instance.text = msg['message']
    print("client_instance.text:", client_instance.text)


# add new
def recv_text(time, user, text):
    socketio.emit('message', {
        "time": time,
        "user": user,
        "message": text
    })


def join_status(status):
    socketio.emit('status', {
        "status": status
    })


def recv_camera(user, frame):
    socketio.emit('video_frame', {
        "user_id": user,
        "frame": frame
    })


def recv_screen(screen_frame):
    socketio.emit('screen_frame', {
        "screen_frame": screen_frame
    })


def recv_host_info(message):
    socketio.emit('host_info', {
        "message": message
    })


def recv_quit(message):
    socketio.emit('quit_info', {
        "message": message
    })

# @socketio.on('me')
# def rev_text(msg):
#     send(msg, broadcast=True)
#     return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

@app.route('/api/box-size', methods=['POST'])
def update_screen_size():
    client_instance = app.config.get('CLIENT_INSTANCE')
    """接收前端传入的边界框大小"""
    # global current_box_size
    data = request.json
    if 'width' in data and 'height' in data:
        util.current_screen_size = data
        print(f"接收到边界框大小：宽: {data['width']}，高: {data['height']}")
        return jsonify({'status': 'success', 'box_size': util.current_screen_size})
    return jsonify({'status': 'error', 'message': '无效的数据'}), 400
