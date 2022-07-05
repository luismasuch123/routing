import math
import os
import pandas as pd
from collections import defaultdict
from operator import itemgetter
import numpy as np
import datetime
from dateutil import parser

def get_common_trips(landmarks, landmark_j, landmark_k, dirPath_edge_id_lists, common_trips):
    '''
    returns the edge_id_lists which contain both landmarks in the order j-k
    '''
    #TODO: zwischen landmarks dürfen keine weiteren landmarks auftauchen
    for file in os.listdir(dirPath_edge_id_lists):
        path = os.path.join(dirPath_edge_id_lists, file)
        df = pd.read_csv(path, names=['ID', 'DAY', 'TIME'], skiprows=[0], sep=" ", skipinitialspace=True)
        landmark_j_found = False
        landmark_k_found = False
        for i, row in df.iterrows():
            if not landmark_k_found:
                if row['ID'] == landmark_j:
                    landmark_j_found = True
                elif row['ID'] == landmark_k and landmark_j_found:
                    key = str(landmark_j) + "-" + str(landmark_k)
                    common_trips[key].append(int(file.replace(".txt", "")))
                    landmark_k_found = True
                elif landmark_j_found and row['ID'] in landmarks and row['ID'] != landmark_k:
                    # zwischen landmarks dürfen sich keine weiteren landmarks befinden, um die travel_time zu schätzen
                    landmark_j_found = False
            else:
                break
    return common_trips

def get_travel_times(landmarks, landmark_j, landmark_k, edge_id_list_extended_path):
    '''
    searches for edge_id_lists which contain both landmarks in the order j-k one or multiple times and computes the travel_time between those landmarks,
    which are then returned
    '''
    # TODO: zwischen landmarks dürfen keine weiteren landmarks auftauchen
    df = pd.read_csv(edge_id_list_extended_path, names=['ID', 'DAY', 'TIME'], skiprows=[0], sep=" ", skipinitialspace=True)
    #Zeilen zusammenführen, um sie dann in datetime umzuwandeln
    df['DATETIME'] = df['DAY'].astype((str)) + " " + df['TIME'].astype(str)
    df.drop('DAY', 1, inplace=True)
    df.drop('TIME', 1, inplace=True)
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce')

    # hier wird die Zeit, die von einer zur anderen landmark benötigt wird(time_delta) und der Startzeitpunkt(day_time) gespeichert
    travel_time = defaultdict(list)
    landmark_j_found_current = False
    for i, row in df.iterrows():
        if row['ID'] == landmark_j:
            landmark_j_found_current = True
            time_j = row['DATETIME']
        elif row['ID'] == landmark_k and landmark_j_found_current:
            time_k = row['DATETIME']
            time_delta = time_k - time_j
            travel_time['delta_time'].append(time_delta)
            travel_time['day_time'].append(time_j)
            landmark_j_found_current = False
        elif landmark_j_found_current and row['ID'] in landmarks and row['ID'] != landmark_k:
            # zwischen landmarks dürfen sich keine weiteren landmarks befinden, um die travel_time zu schätzen
            landmark_j_found_current = False
    #travel_time = {'day time': day_time, 'time delta': time_delta}
    print("travel time: " + str(travel_time))
    return travel_time

def match_gps_points(j, k, streets_path, trip_path):
    #landmark mit dem GPS-Punkt matchen, der zwischen den GPS-Punkten, mit dem kürzesten zeitlichen Abstand,
    #die mit dem landmark_Start und -Ende gematched werden
    streets = pd.read_csv(streets_path, names=['edge ID',
                                              'start nodes ID',
                                              'longitude of start node',
                                              'latitude of start node',
                                              'end nodes ID',
                                              'longitude of end node',
                                              'latitude of end node',
                                              'distance(meters)',
                                              'type of this road',
                                              'angle'],
                                        skiprows=[0], sep=" ", index_col='edge ID')
    street_j = [[streets.loc[j, 'longitude of start node'], streets.loc[j, 'latitude of start node']],
                [streets.loc[j, 'longitude of end node'], streets.loc[j, 'latitude of end node']]]
    print("street j: " + str(street_j))

    street_k = [[streets.loc[k, 'longitude of start node'], streets.loc[k, 'latitude of start node']],
                [streets.loc[k, 'longitude of end node'], streets.loc[k, 'latitude of end node']]]
    print("street k: " + str(street_k))
    #als nächstes Strassen/landmarks mit GPS-Punkt und Zeitpunkt matchen
    gps_log = pd.read_csv(trip_path, names=['Data(UTC)', 'Time(UTC)', 'Latitude', 'Longitude'], skiprows=[0], sep=" ")

    #jeweils mehrere Kandidaten in Liste behalten, falls Zeitpunkt_j for Zeitpunkt_k
    number_candidates = 3
    #nearest_point_j = [number_candidates+1][2] #jeweils Zeile und Entfernung merken
    #nearest_point_k = [number_candidates+1][2]
    nearest_point_j = [[1000000 for i in range(2)] for i in range(number_candidates)]
    nearest_point_k = [[1000000 for i in range(2)] for i in range(number_candidates)]
    #TODO: lieber über len(nearest_point regeln, damit nicht in candidates reinrutscht, falls zu wenige?

    for i, row in gps_log.iterrows():
        #TODO:bezieht sich i auf richtige Zeile? Startet i bei 1 oder 2?
        #street j
        distance_between_start_end_j = math.sqrt(math.pow(street_j[0][0] - street_j[1][0], 2) + math.pow(street_j[0][1] - street_j[1][1], 2))
        #current point
        distance_current_to_start_node_j = math.sqrt(math.pow(street_j[0][0] - row['Longitude'], 2) + math.pow(street_j[0][1] - row['Latitude'], 2))
        distance_current_to_end_node_j = math.sqrt(math.pow(street_j[1][0] - row['Longitude'], 2) + math.pow(street_j[1][1] - row['Latitude'], 2))
        average_distance_current_to_street_j = (distance_current_to_start_node_j + distance_current_to_end_node_j) / 2
        #last point
        if i == 0:
            distance_last_to_end_node_j = distance_current_to_end_node_j
            distance_current_to_last_j = 0
        else:
            distance_last_to_end_node_j = math.sqrt(math.pow(street_j[1][0] - gps_log.loc[i - 1, 'Longitude'], 2) + math.pow(street_j[1][1] - gps_log.loc[i - 1, 'Latitude'], 2))
            distance_current_to_last_j = math.sqrt(math.pow(gps_log.loc[i, 'Longitude'] - row['Longitude'], 2) + math.pow(street_j[1][1] - gps_log.loc[i, 'Latitude'], 2))
        #next point
        if i == len(gps_log)-1:
            distance_next_to_start_node_j = distance_current_to_start_node_j
            distance_current_to_next_j = 0
        else:
            distance_next_to_start_node_j = math.sqrt(math.pow(street_j[0][0] - gps_log.loc[i + 1, 'Longitude'], 2) + math.pow(street_j[0][1] - gps_log.loc[i + 1, 'Latitude'], 2))
            distance_current_to_next_j = math.sqrt(math.pow(gps_log.loc[i + 1, 'Longitude'] - row['Longitude'], 2) + math.pow(street_j[1][1] - gps_log.loc[i + 1, 'Latitude'], 2))

        #street k
        distance_between_start_end_k = math.sqrt(math.pow(street_k[0][0] - street_k[1][0], 2) + math.pow(street_k[0][1] - street_k[1][1], 2))
        #current point
        distance_current_to_start_node_k = math.sqrt(math.pow(street_k[0][0] - row['Longitude'], 2) + math.pow(street_k[0][1] - row['Latitude'], 2))
        distance_current_to_end_node_k = math.sqrt(math.pow(street_k[1][0] - row['Longitude'], 2) + math.pow(street_k[1][1] - row['Latitude'], 2))
        average_distance_current_to_street_k = (distance_current_to_start_node_k + distance_current_to_end_node_k) / 2
        # last point
        if i == 0:
            distance_last_to_end_node_k = distance_current_to_end_node_k
            distance_current_to_last_k = 0
        else:
            distance_last_to_end_node_k = math.sqrt(math.pow(street_k[1][0] - gps_log.loc[i - 1, 'Longitude'], 2) + math.pow(street_k[1][1] - gps_log.loc[i - 1, 'Latitude'], 2))
            distance_current_to_last_k = math.sqrt(math.pow(gps_log.loc[i - 1, 'Longitude'] - row['Longitude'], 2) + math.pow(street_k[1][1] - gps_log.loc[i - 1, 'Latitude'], 2))
        # next point
        if i == len(gps_log)-1:
            distance_next_to_start_node_k = distance_current_to_start_node_k
            distance_current_to_next_k = 0
        else:
            distance_next_to_start_node_k = math.sqrt(math.pow(street_k[0][0] - gps_log.loc[i+1, 'Longitude'], 2) + math.pow(street_k[0][1] - gps_log.loc[i+1, 'Latitude'], 2))
            distance_current_to_next_k = math.sqrt(math.pow(gps_log.loc[i+1, 'Longitude'] - row['Longitude'], 2) + math.pow(street_k[1][1] - gps_log.loc[i+1, 'Latitude'], 2))
        if average_distance_current_to_street_j < nearest_point_j[-1][1]:
            # Abstand zu Start- und Endknoten kleiner ist, als der Abstand zwischen Start- und Endknoten
            if distance_current_to_start_node_j < distance_between_start_end_j and distance_current_to_end_node_j < distance_between_start_end_j:
                # Richtungsbedingung erfüllt
                if distance_last_to_end_node_j > distance_current_to_last_j and distance_next_to_start_node_j > distance_current_to_next_j:
                    nearest_point_j.append([i, average_distance_current_to_street_j])
                    nearest_point_j = sorted(nearest_point_j, key=itemgetter(1))
                    if len(nearest_point_j) > number_candidates:
                        nearest_point_j.pop()
            else: #TODO:anderes Kriterium
                # Richtungsbedingung erfüllt
                if distance_last_to_end_node_j > distance_current_to_last_j and distance_next_to_start_node_j > distance_current_to_next_j:
                    nearest_point_j.append([i, average_distance_current_to_street_j])
                    nearest_point_j = sorted(nearest_point_j, key=itemgetter(1))
                    if len(nearest_point_j) > number_candidates:
                        nearest_point_j.pop()
                        b = nearest_point_j
        if average_distance_current_to_street_k < nearest_point_k[-1][1]:
            # Abstand zu Start- und Endknoten kleiner ist, als der Abstand zwischen Start- und Endknoten
            if distance_current_to_start_node_k < distance_between_start_end_k and distance_current_to_end_node_k < distance_between_start_end_k:
                # Richtungsbedingung erfüllt
                if distance_last_to_end_node_k > distance_current_to_last_k and distance_next_to_start_node_k > distance_current_to_next_k:
                    nearest_point_k.append([i, average_distance_current_to_street_k])
                    nearest_point_k = sorted(nearest_point_k, key=itemgetter(1))
                    if len(nearest_point_k) > number_candidates:
                        nearest_point_k.pop()
            else: #TODO:anderes Kriterium
                # Richtungsbedingung erfüllt
                if distance_last_to_end_node_k > distance_current_to_last_k and distance_next_to_start_node_k > distance_current_to_next_k:
                    nearest_point_k.append([i, average_distance_current_to_street_k])
                    nearest_point_k = sorted(nearest_point_k, key=itemgetter(1))
                    if len(nearest_point_k) > number_candidates:
                        nearest_point_k.pop()

    print("nearest point j: " + str(nearest_point_j))
    print("nearest point k: " + str(nearest_point_k))
    #prüfen ob nearest_point_j vor nearest_point_k befahren wurde bzw. nach diesem Kriterium aus Kandidaten auswählen
    gps_points = dict.fromkeys(["time_j", "longitude_j", "latitude_j", "time_k", "longitude_k", "latitude_k"])
    points_found = False
    a = 0
    b = 0
    if gps_log.loc[nearest_point_j[a][0], 'Time(UTC)'] < gps_log.loc[nearest_point_k[b][0], 'Time(UTC)']:
        points_found = True
    while (not points_found) and a < number_candidates and b < number_candidates:
        if nearest_point_j[a][1] > nearest_point_k[b][1]:
            if gps_log.loc[nearest_point_j[a][0], 'Time(UTC)'] < gps_log.loc[nearest_point_k[b+1][0], 'Time(UTC)']:
                points_found = True
            b += 1
        else:
            if gps_log.loc[nearest_point_j[a+1][0], 'Time(UTC)'] < gps_log.loc[nearest_point_k[b][0], 'Time(UTC)']:
                points_found = True
            a += 1
    if points_found:
        gps_points["time_j"] = gps_log.loc[nearest_point_j[a][0], 'Time(UTC)']
        gps_points["longitude_j"] = gps_log.loc[nearest_point_j[a][0], 'Longitude']
        gps_points["latitude_j"] = gps_log.loc[nearest_point_j[a][0], 'Latitude']
        gps_points["time_k"] = gps_log.loc[nearest_point_k[a][0], 'Time(UTC)']
        gps_points["longitude_k"] = gps_log.loc[nearest_point_k[a][0], 'Longitude']
        gps_points["latitude_k"] = gps_log.loc[nearest_point_k[a][0], 'Latitude']
    else:
        print("No feasible pair of points matching landmarks found!")
        #TODO: Exception

    #falls mehrmals befahren (durch common_trips überprüfbar) Uhrzeiten beachten, Achtung Richtung beachten!
    return gps_points

def estimate_travel_times(landmarks, dirPath_edge_id_lists):
    travel_time = defaultdict(lambda: defaultdict(list))
    common_trips = defaultdict(list)
    for j in range(len(landmarks)):
        for k in range(len(landmarks)):
            if j is not k:
                common_trips = get_common_trips(landmarks, landmarks[j], landmarks[k], dirPath_edge_id_lists, common_trips)

    for key in common_trips:
        landmark_j = int(key.split("-")[0])
        landmark_k = int(key.split("-")[1])
        for value in common_trips[key]:
            #trip_path = os.path.join(dirPath_logs, str(value) + ".txt")
            edge_id_list_extended_path = os.path.join(dirPath_edge_id_lists, str(value) + ".txt")
            travel_time[key] = get_travel_times(landmarks, landmark_j, landmark_k, edge_id_list_extended_path)
    print("common trips: " + str(common_trips))
    print("travel time: " + str(travel_time))
    #TODO: V-Clustering
    #Liste mit allen travel_times in travel_time
    L_datetimes = []
    for key in travel_time:
        for value in travel_time[key]['delta_time']:
            L_datetimes.append(value)
    L_datetimes.sort()
    print(L_datetimes)
    # convert datetimes to seconds
    L_seconds = []
    for l in L_datetimes:
        L_seconds.append(datetime.timedelta(l).total_seconds()) #TODO: hier weitermachen
    print(L_seconds)
    variance_L = np.var(L_seconds)
    print(variance_L)
    #TODO: set treshold

    #TODO: VE-Clustering