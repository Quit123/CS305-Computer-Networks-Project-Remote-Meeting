import asyncio
from util import *


class ConferenceServer:
    def __init__(self, conference_id, conf_serve_ports):
        # async server
        self.conference_id = conference_id  # conference_id for distinguish difference conference
        self.conf_serve_ports = conf_serve_ports
        self.data_serve_ports = {8001,8002,8003}
        self.data_types = ['audio','screen', 'camera']  # example data types in a video conference
        self.clients_info = {}
        self.client_conns = {}
        self.mode = 'Client-Server'  # or 'P2P' if you want to support peer-to-peer conference mode
        self.run = True

    async def handle_data(self, reader, writer, data_type):
        """
        running task: receive sharing stream data from a client and decide how to forward them to the rest clients
        """
        while self.run:
            data = await reader.read(100)
            if not data:
                break
            for client_writer in self.client_conns.values():
                if client_writer != writer:
                    client_writer.write(data)
                    await client_writer.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_client(self, reader, writer):
        """
        running task: handle the in-meeting requests or messages from clients
        """
        while self.run:
            message = await reader.read(100)
            if not message:
                break
            # Handle different types of messages here
            # For example, if a client wants to share their screen, start a handle_data task
            # if message == b'start_screen_share':
            #     asyncio.create_task(self.handle_data(reader, writer, 'screen'))
        writer.close()
        await writer.wait_closed()

    async def log(self):
        while self.run:
            print('Something about server status')
            await asyncio.sleep(LOG_INTERVAL)

    async def cancel_conference(self):
        """
        handle cancel conference request: disconnect all connections to cancel the conference
        """
        self.run = False
        for writer in self.client_conns.values():
            writer.close()
            await writer.wait_closed()
        self.client_conns.clear()

    def start(self):
        '''
        start the ConferenceServer and necessary running tasks to handle clients in this conference
        '''
        loop = asyncio.get_event_loop()
        for data_type, port in self.conf_serve_ports.items():
            server = asyncio.start_server(self.handle_client, '127.0.0.1', port, loop=loop)
            loop.run_until_complete(server)
        loop.create_task(self.log())
        loop.run_forever()

class MainServer:
    def __init__(self, server_ip, main_port):
        # async server
        self.server_ip = server_ip
        self.server_port = main_port
        self.main_server = None

        self.conference_conns = None
        self.conference_servers = {}  # self.conference_servers[conference_id] = ConferenceManager

    def handle_creat_conference(self,):
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client
        """

    def handle_join_conference(self, conference_id):
        """
        join conference: search corresponding conference_info and ConferenceServer, and reply necessary info to client
        """

    def handle_quit_conference(self):
        """
        quit conference (in-meeting request & or no need to request)
        """
        pass

    def handle_cancel_conference(self):
        """
        cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
        """
        pass

    async def request_handler(self, reader, writer):
        """
        running task: handle out-meeting (or also in-meeting) requests from clients
        """
        pass

    def start(self):
        """
        start MainServer
        """
        pass


if __name__ == '__main__':
    server = MainServer(SERVER_IP, MAIN_SERVER_PORT)
    server.start()
