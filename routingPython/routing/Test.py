"""
Script to run the T-Drive algorithm on an edge_id_list resulting from the map matching.
"""
import os
import pandas as pd
from build_landmark_graph import get_k_landmarks
from travel_time_estimation import estimate_travel_times

dirPath_edge_id_lists = '/Users/luismasuchibanez/PycharmProjects/t_drive/routing/routingPython/data/Melbourne/edge_id_list_test_time'
dirPath_logs = '/Users/luismasuchibanez/PycharmProjects/t_drive/routing/routingPython/data/Melbourne/taxi_log'
#streets_path = '/Users/luismasuchibanez/PycharmProjects/t_drive/routing/routingPython/data/Melbourne/complete-osm-map/streets.txt'

#TODO: add a query
number_landmarks = 3

#TODO: compute frequency of e
#TODO: set minimum frequency treshold to remove the landmark edges having a very long travel time
#TODO: set tmax
landmarks = get_k_landmarks(number_landmarks, dirPath_edge_id_lists) #zunächst werden top-k road segments gewählt
print("landmarks: " + str(landmarks))
#landmarks werden verknüpft, wobei weitere Kriterien berücksichtigt werden
#tau = compute_tau(dirPath_logs)
estimate_travel_times(landmarks, dirPath_edge_id_lists)

#TODO: rough routing
#TODO: refined routing


