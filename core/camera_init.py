import cv2
from core.cam_fresh import FreshestFrame
import yaml


with open('./config/ip_cam_config.yaml', 'r') as config_file:
    ip_config_data = yaml.safe_load(config_file)


fresh = FreshestFrame(
    ip_config_data['ip_cam_address']
    # cv2.VideoCapture(ip_config_data['ip_cam_address'])
)


# fresh = FreshestFrame(
#     cv2.VideoCapture(0)
# )