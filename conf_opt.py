import asyncio
from conf_client import *
from util import *


async def establish_connect(self):
    try:
        for type in self.support_data_types:
            port = self.ports.get(type)
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


async def receive_text(self, decompress=None):
    print("[Info]: Starting text playback monitoring...")
    reader, writer = self.sockets['text']
    while self.on_meeting:
        text_chunk = await reader.read(CHUNK)
        self.data_queues['text'].put_nowait(text_chunk)


async def output_data(self, fps_or_frequency):
    """
        running task: output received stream data
        """
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
        if not self.data_queues['audio'].empty():
            pass
        if not self.data_queues['text'].empty():
            received_message = self.text_queue.get()
            try:
                with open('user_commands.txt', 'a', encoding='utf-8') as f:
                    f.write(received_message)
            except Exception as e:
                print(f"upload entry error: {e}")

        await asyncio.sleep(1 / fps_or_frequency)


async def send_datas(self):
    await asyncio.gather(send_texts(self), send_audio(self))

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


async def send_audio(self):
    while self.is_working and self.on_meeting:
        if not self.acting_data_types['audio']:
            await asyncio.sleep(0)
            continue
        print("[Info]: Starting audio transmission...")
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
        print("[Info]: Audio is closing.")
