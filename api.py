from flask import Flask, request, jsonify
import asyncio
import util

app = Flask(__name__)
client_instance = app.config.get('CLIENT_INSTANCE')


@app.route('/register', methods=['POST'])
def register():
    """前端通过 POST 请求更新 text 状态"""
    # client_instance.share_switch('audio')
    # return jsonify({'status': 'success', 'audio_status': client_instance.acting_data_types['audio']})


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
