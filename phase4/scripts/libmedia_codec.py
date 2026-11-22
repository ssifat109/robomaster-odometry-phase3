"""PyAV-compatible video decoder for DJI SDK on modern Linux.

The SDK imports this top-level module. Its old native codec does not build on
Python 3.12 / FFmpeg 6, so this supplies the small interface used by media.py.
Audio is intentionally unsupported because Phase 4 records video frames only.
"""
import av


class H264Decoder:
    def __init__(self):
        self.codec = av.CodecContext.create('h264', 'r')

    def decode(self, data):
        output = []
        for packet in self.codec.parse(data):
            for frame in self.codec.decode(packet):
                array = frame.to_ndarray(format='bgr24')
                output.append((array.tobytes(), array.shape[1], array.shape[0],
                               array.shape[1] * 3))
        return output


class OpusDecoder:
    def decode(self, data):
        raise RuntimeError('Audio decoding is not used in Phase 4')
