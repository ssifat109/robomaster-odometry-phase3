"""Connect to EP Core AP using the interface routed to 192.168.2.1."""
import socket


def connect(cfg):
    import numpy as np
    from robomaster import config as sdk_config, conn, media, robot

    def decode_h264(self, data):
        frames = []
        for frame, width, height, _ in self._video_decoder.decode(data):
            if frame:
                frames.append(np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 3))
        return frames

    # DJI's media.py uses NumPy's removed binary fromstring mode.
    media.LiveView._h264_decode = decode_h264
    if cfg['robot_connection_type'] == 'ap':
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(('192.168.2.1', 20020))
            sdk_config.LOCAL_IP_STR = sock.getsockname()[0]
    # DJI SDK compares these strings by identity, so pass its own constants.
    modes = {'ap': conn.CONNECTION_WIFI_AP, 'sta': conn.CONNECTION_WIFI_STA}
    ep = robot.Robot()
    if not ep.initialize(conn_type=modes[cfg['robot_connection_type']]):
        raise RuntimeError('RoboMaster SDK connection failed')
    return ep
