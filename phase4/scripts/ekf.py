"""Bearing-only EKF for a fixed landmark and odometry increments."""
import math
import numpy as np


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def bearing(state, cfg):
    x, y, heading = state
    c, s = math.cos(heading), math.sin(heading)
    cx = x + c * cfg['camera_x_m'] - s * cfg['camera_y_m']
    cy = y + s * cfg['camera_x_m'] + c * cfg['camera_y_m']
    return wrap(math.atan2(cfg['tag_y_m'] - cy, cfg['tag_x_m'] - cx)
                - heading - cfg['camera_yaw_rad'])


def bearing_jacobian(state, cfg):
    x, y, th = state
    c, s = math.cos(th), math.sin(th)
    ax, ay = cfg['camera_x_m'], cfg['camera_y_m']
    cx, cy = x + c * ax - s * ay, y + s * ax + c * ay
    dx, dy = cfg['tag_x_m'] - cx, cfg['tag_y_m'] - cy
    r2 = dx * dx + dy * dy
    if r2 < 0.01:
        raise ValueError('Tag too close to camera for a stable bearing update')
    dcx = -s * ax - c * ay
    dcy = c * ax - s * ay
    return np.array([[dy / r2, -dx / r2,
                      (dy * dcx - dx * dcy) / r2 - 1.0]])


class BearingEKF:
    def __init__(self, cfg):
        self.cfg = cfg
        self.x = np.array([cfg['initial_x_m'], cfg['initial_y_m'],
                           cfg['initial_heading_rad']], dtype=float)
        self.P = np.diag([cfg['initial_std_x_m'] ** 2,
                          cfg['initial_std_y_m'] ** 2,
                          math.radians(cfg['initial_std_heading_deg']) ** 2])
        self.Q = np.diag([cfg['motion_std_x_m_per_step'] ** 2,
                          cfg['motion_std_y_m_per_step'] ** 2,
                          math.radians(cfg['motion_std_heading_deg_per_step']) ** 2])
        self.R = math.radians(cfg['bearing_std_deg']) ** 2

    def predict(self, forward, left, dtheta):
        th = self.x[2]
        c, s = math.cos(th), math.sin(th)
        self.x[0] += c * forward - s * left
        self.x[1] += s * forward + c * left
        self.x[2] = wrap(th + dtheta)
        F = np.array([[1, 0, -s * forward - c * left],
                      [0, 1, c * forward - s * left], [0, 0, 1]])
        self.P = F @ self.P @ F.T + self.Q
        self.P = (self.P + self.P.T) / 2

    def update(self, observed_bearing):
        H = bearing_jacobian(self.x, self.cfg)
        innovation = wrap(observed_bearing - bearing(self.x, self.cfg))
        S = (H @ self.P @ H.T).item() + self.R
        K = self.P @ H.T / S
        self.x += K[:, 0] * innovation
        self.x[2] = wrap(self.x[2])
        I_KH = np.eye(3) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + self.R * (K @ K.T)
        self.P = (self.P + self.P.T) / 2
        return K[:, 0], innovation


def camera_bearing_from_tag(center_x, image_width, cfg):
    """Pinhole projection from normalized horizontal image center to angle."""
    if 'camera_fx_px' in cfg:
        scale = image_width / cfg['camera_calibration_width_px']
        fx = cfg['camera_fx_px'] * scale
        cx = cfg['camera_cx_px'] * scale
        return -math.atan((center_x - cx) / fx)
    f = (image_width / 2) / math.tan(math.radians(cfg['camera_horizontal_fov_deg']) / 2)
    # Image x increases to the right; positive robot bearing is to the left.
    return -math.atan((center_x - image_width / 2) / f)
