import json
from pathlib import Path
import cv2
import numpy

root = Path(__file__).resolve().parents[1]
cfg = json.loads((root / 'config.json').read_text())
assert cfg['tag_id'] in range(50)
assert cfg['tag_size_m'] > 0
assert cfg['forward_speed_mps'] > 0 and cfg['duration_s'] > 0
assert cfg['bearing_std_deg'] > 0
assert hasattr(cv2, 'aruco'), 'Install opencv-contrib-python.'
print('OpenCV', cv2.__version__, '| NumPy', numpy.__version__)
print('Config valid. Tag:', cfg['tag_id'], '| target:', (cfg['tag_x_m'], cfg['tag_y_m']))
print('Verify every physical dimension and camera FOV before robot runs.')
