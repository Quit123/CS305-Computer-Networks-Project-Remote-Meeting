from flask import Flask, request, jsonify
import asyncio
from conf_client import *

client_instance = ConferenceClient()


@app.route('/update-audio-status', methods=['POST'])
def update_text_status():
    """前端通过 POST 请求更新 text 状态"""
    client_instance.share_switch('audio')
    return jsonify({'status': 'success', 'audio_status': client_instance.acting_data_types['text']})


@app.route('/send-text', methods=['POST'])
def send_text():
    """前端通过 POST 请求发送文本消息"""
    data = request.json
    if 'message' in data:
        client_instance.text = data['message']
        client_instance.text_event.set()
        return jsonify({'status': 'success', 'message': client_instance.text})
    return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
