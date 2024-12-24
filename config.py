HELP = 'Create         : create an conference\n' \
       'Join [conf_id ]: join a conference with conference ID\n' \
       'Quit           : quit an on-going conference\n' \
       'Cancel         : cancel your on-going conference (only the manager)\n\n'


SERVER_IP = '192.168.3.8'
MAIN_SERVER_PORT = 9000
TIMEOUT_SERVER = 5
# DGRAM_SIZE = 1500  # UDP
LOG_INTERVAL = 2

CHUNK = 10240
CHANNELS = 1  # Channels for audio capture
RATE = 44100  # Sampling rate for audio capture
BUFF_SIZE = 65536

camera_width, camera_height = 480, 480  # resolution for camera capture

internal_protocol = {
       'function': None,
       'User': None,
       'Length': None,
       'message': None,
}
