import os
import pandas as pd
from build_landmark_graph import get_k_landmarks
from travel_time_estimation import estimate_travel_times

dirPath_edge_id_lists = '/Users/luismasuchibanez/PycharmProjects/t_drive/routing/routingPython/data/Melbourne/edge_id_list_test'
dirPath_logs = '/Users/luismasuchibanez/PycharmProjects/t_drive/routing/routingPython/data/Melbourne/taxi_log_test'
streets_path = '/Users/luismasuchibanez/PycharmProjects/t_drive/routing/routingPython/data/Melbourne/complete-osm-map/streets.txt'

number_landmarks = 2

landmarks = get_k_landmarks(number_landmarks, dirPath_edge_id_lists)
print("landmarks: " + str(landmarks))
estimate_travel_times(landmarks, dirPath_edge_id_lists, streets_path, dirPath_logs)

