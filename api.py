from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send
import asyncio
import util
from log_register_func import *
from flask_cors import CORS

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
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


# @app.route('/api/init', methods=['POST'])
# def init():
#     """Handle POST request for user login"""
#     global established_client
#     client1 = ConferenceClient()
#     established_client, info = connection_establish(client1.server_addr)
#     app.config['CLIENT_INSTANCE'] = client1
#     app.run(debug=False)

# 具体功能之后完善

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
    recv = server_message_encrypt(use_input, client_instance)
    if "Login successfully" in recv:
        login_info["status"] = True
        client_instance.user_name = username
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
async def Create():
    print("click Create")
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    # global create
    # create = True
    data = request.json
    title = data.get('title')
    title = title + " " + client_instance.user_name
    ans, con_id = await client_instance.create_conference(title)
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
async def Join():
    print("click Join")
    client_instance = app.config.get('CLIENT_INSTANCE')
    """Handle POST request for user login"""
    con_in = request.json
    con_id = con_in['con_id']
    print(con_id)
    con_id = con_id + " " + client_instance.user_name
    await client_instance.join_conference(con_id)
    # if username in users and users[username] == password:
    # error = 0
    # while not client_instance.on_meeting:
    #     if "Error" in ans:
    #         error = 1
    #         break
    # if error == 0:
    #     return jsonify({'status': 'success', 'message': ans})
    # else:
    #     return jsonify({'status': 'fail', 'message': ans})


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
    client_instance.cancel_conference()
    # if username in users and users[username] == password:
    return jsonify({'status': 'success', 'message': 'Click cancel return'})


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


@socketio.on('message')
def send_text(msg):
    # 自己发送的信息要传用户名
    # server发送的信息需要特殊标识一下
    send(msg, broadcast=True)
    client_instance = app.config.get('CLIENT_INSTANCE')
    """前端通过 POST 请求发送文本消息"""
    if 'message' in msg:
        client_instance.text = msg['message']
        print("client_instance.text:", client_instance.text)
        client_instance.text_event.set()
        return jsonify({'status': 'success', 'message': client_instance.text})
    return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
    #client_instance = app.config.get('CLIENT_INSTANCE')


@socketio.on('message')
def rev_text(msg):
    send(msg, broadcast=True)
    return jsonify({'status': 'error', 'message': 'Invalid data'}), 400


# @app.route('/api/send', methods=['POST'])
# def send_text():
#     client_instance = app.config.get('CLIENT_INSTANCE')
#     """前端通过 POST 请求发送文本消息"""
#     data = request.json
#     if 'message' in data:
#         client_instance.text = data['message']
#         client_instance.text_event.set()
#         return jsonify({'status': 'success', 'message': client_instance.text})
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
