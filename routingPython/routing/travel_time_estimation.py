import math
import os
import pandas as pd
from collections import defaultdict
from operator import itemgetter
import numpy as np
import datetime
from dateutil import parser
import matplotlib.pyplot as plt

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
                    #TODO: filename global definieren
                    common_trips[key].append(int(file.replace("Beijing_IVMM_matching_result_", "").replace("_.txt", "")))
                    landmark_k_found = True
                elif landmark_j_found and row['ID'] in landmarks and row['ID'] != landmark_k:
                    # zwischen landmarks dürfen sich keine weiteren landmarks befinden, um die travel_time zu schätzen
                    landmark_j_found = False
            else:
                break
    return common_trips

def get_travel_times(travel_time, landmarks, landmark_j, landmark_k, edge_id_list_extended_path):
    '''
    searches for edge_id_lists which contain both landmarks in the order j-k one or multiple times and computes the travel_time between those landmarks,
    which are then returned
    '''
    df = pd.read_csv(edge_id_list_extended_path, names=['ID', 'DAY', 'TIME'], skiprows=[0], sep=" ", skipinitialspace=True)
    #Zeilen zusammenführen, um sie dann in datetime umzuwandeln
    df['DATETIME'] = df['DAY'].astype((str)) + " " + df['TIME'].astype(str)
    df.drop('DAY', 1, inplace=True)
    df.drop('TIME', 1, inplace=True)
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce')

    # hier wird die Zeit, die von einer zur anderen landmark benötigt wird(time_delta) und der Startzeitpunkt(day_time) gespeichert
    ##travel_time = defaultdict(list)
    landmark_j_found_current = False
    for i, row in df.iterrows():
        if row['ID'] == landmark_j:
            landmark_j_found_current = True
            time_j = row['DATETIME']
        elif row['ID'] == landmark_k and landmark_j_found_current:
            time_k = row['DATETIME']
            time_delta = time_k - time_j
            #TODO: Was ist der Grund dafür, dass time_delta gleich 0 ist und können diese Werte einfach aussortiert werden?
            if time_delta > datetime.timedelta(seconds=0):
                travel_time['delta_time'].append(time_delta)
                travel_time['day_time'].append(time_j)
            landmark_j_found_current = False
        elif landmark_j_found_current and row['ID'] in landmarks and row['ID'] != landmark_k:
            # zwischen landmarks dürfen sich keine weiteren landmarks befinden, um die travel_time zu schätzen
            landmark_j_found_current = False
    return travel_time

def compute_entropies(travel_time, L, v_cluster_indeces, v_cluster_values, S_help, number_partitions):
    p_i = [0 for ci in range(len(L))]
    entropy_S = [0 for p in range(number_partitions + 1)]
    v_cluster_counter = [[0 for l in range(len(L))] for p in range(number_partitions + 1)]
    for ci in range(len(v_cluster_indeces)):
        # innerhalb der Partition bestimmen wie groß der Anteil der verschiedenen V-Clustertypen ist
        # für alle travel_times mit hours <= hours(i) Clustertypen zählen und daraus p_i's ableiten
        for value in travel_time['day_time']:
            index_value = travel_time['day_time'].index(value)
            hour = value.hour + value.minute / 60 + value.second / 3600
            if ci == 0:
                for s in range(number_partitions + 1):
                    if hour in S_help[s] and travel_time['delta_time'][index_value].total_seconds() <= v_cluster_values[ci]:
                        v_cluster_counter[s][ci] += 1
            elif ci < len(v_cluster_indeces):
                if hour in S_help[0] and travel_time['delta_time'][index_value].total_seconds() > \
                        v_cluster_values[ci - 1] and travel_time['delta_time'][index_value].total_seconds() <= \
                        v_cluster_values[ci]:
                    v_cluster_counter[0][ci] += 1
                for p in range(1, number_partitions + 1):
                    if hour in S_help[p] and travel_time['delta_time'][index_value].total_seconds() <= v_cluster_values[ci]:
                        v_cluster_counter[p][ci] += 1
        for s in range(len(S_help)):
            p_i[ci] = v_cluster_counter[s][ci] / len(S_help[s])
            if p_i[ci] > 0:
                entropy_S[s] -= p_i[ci] * math.log(p_i[ci])
    return entropy_S, v_cluster_counter, p_i



def estimate_travel_times(landmarks, dirPath_edge_id_lists):
    common_trips = defaultdict(list)
    for j in range(len(landmarks)):
        for k in range(len(landmarks)):
            if j is not k:
                common_trips = get_common_trips(landmarks, landmarks[j], landmarks[k], dirPath_edge_id_lists, common_trips)

    cluster = {} #Speicherung der Cluster sowie der dazugehörigen Auftrittwahrscheinlichkeiten
    #TODO: herausfinden, wie treshold gesetzt werden muss, ansonsten manuell begrenzen
    set_cluster_limit = True
    v_cluster_limit = 4 #max. 3 Gruppen
    e_cluster_limit = 7 # max. 6 Gruppen
    for key in common_trips:
        travel_time = defaultdict(list) #Zeiten zwischen landmarks werden hier abgespeichert
        print("common trip: " + str(key))
        landmark_j = int(key.split("-")[0])
        landmark_k = int(key.split("-")[1])
        for value in common_trips[key]:
            #TODO: filename global festlegen, sodass nicht jedes mal angepasst werden muss
            edge_id_list_extended_path = os.path.join(dirPath_edge_id_lists, "Beijing_IVMM_matching_result_" + str(value) + "_.txt")
            travel_time = get_travel_times(travel_time, landmarks, landmark_j, landmark_k, edge_id_list_extended_path)
        print("common trips: " + str(common_trips))
        print("travel time: " + str(travel_time))
        #TODO: V-Clustering auslagern?
        cluster[key] = {}
        #es wird nur geclustert, falls mehr als eine Fahrt auf der landmark_edge durchgeführt wurde
        if (len(travel_time['delta_time']) > 1):
            L_datetimes = [] #Speicherung der Zeit, welche für die Route zwischen zwei landmarks benötigt wird
            for value in travel_time['delta_time']:
                L_datetimes.append(value)
            L_datetimes.sort()
            # convert datetimes to seconds
            L_seconds = [] #L_datetimes in Sekunden umgewandelt
            for l in L_datetimes:
                L_seconds.append(l.total_seconds())
            variance_L = np.var(L_seconds)
            bigger_than_treshold = True
            treshold = 2.0 #TODO: worauf treshold setzen?
            v_cluster_indeces = []
            v_cluster_values = []
            L = [] #Partitionen des V-Clustering
            L_help = [] #Hilfsarray
            number_partitions = 1
            while bigger_than_treshold and len(L_help) < len(L_seconds) and set_cluster_limit and number_partitions < v_cluster_limit:
                WAV_i_L = []
                for i in range(len(L_seconds)-1):
                    if i not in v_cluster_indeces:
                        L_help = L.copy()
                        if number_partitions == 1:
                            L_help.insert(0, L_seconds[0:i+1])
                            L_help.insert(1, L_seconds[i+1:len(L_seconds)])
                            WAV_i_L.append((len(L_help[0]) / len(L_seconds)) * np.var(L_help[0]) + (len(L_help[1]) / len(L_seconds)) * np.var(L_help[1]))
                        else:
                            for p in range(number_partitions-1):
                                if (p == 0 and i <= v_cluster_indeces[p]) or i > v_cluster_indeces[p-1]:
                                    L_help = L.copy()
                                    modification = False
                                    if i < v_cluster_indeces[p] and p == 0:
                                        modification = True
                                        L_help[p] = L_seconds[i+1:v_cluster_indeces[p]+1]
                                        L_help.insert(p, L_seconds[0:i+1])
                                    elif i < v_cluster_indeces[p]:
                                        modification = True
                                        L_help[p] = L_seconds[i+1:v_cluster_indeces[p]+1]
                                        L_help.insert(p, L_seconds[v_cluster_indeces[p-1]+1:i+1])
                                    elif i > v_cluster_indeces[p] and p == number_partitions-2:
                                        modification = True
                                        L_help.append(L_seconds[i+1:len(L_seconds)])
                                        L_help[p+1] = L_seconds[v_cluster_indeces[p]+1:i+1]
                                    if modification:
                                        WAV_i_L_sum = 0
                                        for l in range(len(L_help)):
                                            WAV_i_L_sum += (len(L_help[l]) / len(L_seconds)) * np.var(L_help[l])
                                        WAV_i_L.append(WAV_i_L_sum)
                    else:
                        WAV_i_L.append(1000000000000)
                if WAV_i_L.index(min(WAV_i_L)) not in v_cluster_indeces:
                    v_cluster_indeces.append(WAV_i_L.index(min(WAV_i_L))) #bester Split Indeces: i-tes Element gehört noch zu L_2 seconds
                    v_cluster_indeces.sort()
                    v_cluster_values = []
                    for ci in v_cluster_indeces:
                        v_cluster_values.append(L_seconds[ci])  # bester Split Werte: i-tes Element gehört noch zu L_2 seconds
                    v_cluster_values.sort()
                    #L updaten, d.h. neuen v_cluster_index berücksichtigen
                    L.clear()
                    L.append(L_seconds[0:v_cluster_indeces[0]+1])
                    for p in range(1, number_partitions):
                        L.append(L_seconds[v_cluster_indeces[p-1]+1: v_cluster_indeces[p]+1])
                    L.append(L_seconds[v_cluster_indeces[number_partitions-1]+1:len(L_seconds)])
                    #print("v_cluster_indeces: " + str(v_cluster_indeces))
                    #print("v_cluster_values: " + str(v_cluster_values))
                    if min(WAV_i_L) < treshold:
                        bigger_than_treshold = False
                        #print("min(WAV_i_L) < treshold")
                    else:
                        number_partitions += 1
                        #print("min(WAV_i_L) >= treshold")
                else: #wenn zum zweiten Mal an der selben Stelle geclustert werden soll, wird das WAV_i_L hochgesetzt, um den Schritt zu verhindern
                    WAV_i_L[WAV_i_L.index(min(WAV_i_L))] = 10000000000000
                    if min(WAV_i_L) < treshold:
                        bigger_than_treshold = False
                        #print("min(WAV_i_L) < treshold")
            #TODO: set treshold
            #TODO: VE-Clustering auslagern?
            S_arriving_times = [] #Speicherung der Ankunftszeiten
            for value in travel_time['day_time']:
                S_arriving_times.append(value)
            S_arriving_times.sort()
            # convert datetimes to seconds
            S_hours = []
            for s in S_arriving_times:
                S_hours.append(s.hour + s.minute / 60 + s.second / 3600)

            entropy_S = 0
            for i in v_cluster_indeces:
                p_i = (i+1) / len(L_seconds)
                if p_i > 0:
                    entropy_S -= p_i * math.log(p_i)

            bigger_than_treshold = True
            treshold = 0.5  # TODO: worauf treshold setzen?
            e_cluster_indeces = []
            S = [] #Partitionen des V-Clustering
            S_help = [] #Hilfsarray
            number_partitions = 1
            while bigger_than_treshold and len(S_help) < len(S_hours) and set_cluster_limit and number_partitions < e_cluster_limit:
                WAE_i_S = []
                for i in range(len(S_hours)-1):
                    if i not in e_cluster_indeces:
                        S_help = S.copy()
                        if number_partitions == 1:
                            S_help.insert(0, S_hours[0:i+1])
                            S_help.insert(1, S_hours[i+1:len(S_hours)])
                            entropy_S, v_cluster_counter, p_i = compute_entropies(travel_time, L, v_cluster_indeces, v_cluster_values, S_help, number_partitions)
                        else:
                            for p in range(number_partitions-1):
                                if (p == 0 and i <= e_cluster_indeces[p]) or i > e_cluster_indeces[p-1]:
                                    S_help = S.copy()
                                    modification = False
                                    if i < e_cluster_indeces[p] and p == 0:
                                        modification = True
                                        S_help[p] = S_hours[i+1:e_cluster_indeces[p]+1]
                                        S_help.insert(p, S_hours[0:i+1])
                                        entropy_S, v_cluster_counter, p_i = compute_entropies(travel_time, L, v_cluster_indeces, v_cluster_values, S_help, number_partitions)
                                    elif i < e_cluster_indeces[p]:
                                        modification = True
                                        S_help[p] = S_hours[i+1:e_cluster_indeces[p]+1]
                                        S_help.insert(p, S_hours[e_cluster_indeces[p-1]+1:i+1])
                                        entropy_S, v_cluster_counter, p_i = compute_entropies(travel_time, L, v_cluster_indeces, v_cluster_values, S_help, number_partitions)
                                    elif i > e_cluster_indeces[p] and p == number_partitions-2:
                                        modification = True
                                        S_help.append(S_hours[i+1:len(S_hours)])
                                        S_help[p+1] = S_hours[e_cluster_indeces[p]+1:i+1]
                                        entropy_S, v_cluster_counter, p_i = compute_entropies(travel_time, L, v_cluster_indeces, v_cluster_values, S_help, number_partitions)
                        if modification:
                            WAE_i_S_sum = 0
                            # p_i für letztes v_cluster und entropy bestimmen
                            for s in range(len(S_help)):
                                p_i[len(L) - 1] = (len(S_help[s]) - sum(v_cluster_counter[s])) / len(S_help[s])
                                if p_i[len(L) - 1] > 0:
                                    entropy_S[s] -= p_i[len(L) - 1] * math.log(p_i[len(L) - 1])
                                WAE_i_S_sum += (len(S_help[s]) / len(S_hours)) * entropy_S[s]
                            WAE_i_S.append(WAE_i_S_sum)
                    else:
                        WAE_i_S.append(100000)
                e_cluster_indeces.append(WAE_i_S.index(min(WAE_i_S))) #bester Split Indeces: i-tes Element gehört noch zu L_2 seconds
                e_cluster_indeces.sort()
                e_cluster_values = []
                for ci in e_cluster_indeces:
                    e_cluster_values.append(S_hours[ci])  # bester Split Werte: i-tes Element gehört noch zu L_2 seconds
                e_cluster_values.sort()
                #S updaten, d.h. neuen e_cluster_index berücksichtigen
                S.clear()
                S.append(S_hours[0:e_cluster_indeces[0]+1])
                for p in range(1, number_partitions):
                    S.append(S_hours[e_cluster_indeces[p-1]+1: e_cluster_indeces[p]+1])
                S.append(S_hours[e_cluster_indeces[number_partitions-1]+1:len(S_hours)])
                #print("e_cluster_indeces: " + str(e_cluster_indeces))
                #print("e_cluster_values: " + str(e_cluster_values))
                if min(WAE_i_S) < treshold:
                    bigger_than_treshold = False
                    #print("min(WAV_i_S) < treshold")
                else:
                    number_partitions += 1
                    #print("min(WAV_i_S) >= treshold")
            # TODO: set treshold
            cluster_counter = [[0 for j in range(len(v_cluster_values) + 1)] for i in range(len(e_cluster_values) + 1)]
            e_cluster_counter = [0] * (len(e_cluster_values) + 1)
            for value in travel_time['delta_time']:
                e_cluster = 0
                day_time = travel_time['day_time'][travel_time['delta_time'].index(value)]
                day_time_hours = day_time.hour + day_time.minute / 60 + day_time.second / 3600
                #TODO: welche Grenzen der Intervalle sind inbegriffen und welche nicht?
                while e_cluster < len(e_cluster_values) and e_cluster_values[e_cluster] < day_time_hours:
                    e_cluster += 1
                e_cluster_counter[e_cluster] += 1

                v_cluster = 0
                delta_time_seconds = value.total_seconds()
                while v_cluster < len(v_cluster_values) and v_cluster_values[v_cluster] < delta_time_seconds:
                    v_cluster += 1
                cluster_counter[e_cluster][v_cluster] += 1
                #print("e cluster counter: " + str(e_cluster_counter))
                #print("cluster_counter: " + str(cluster_counter))
            for i in range(len(e_cluster_values)+1):
                for j in range(len(v_cluster_values)+1):
                    a = ''
                    b = ''
                    if i == 0 and j == 0:
                        a = '0-' + str(e_cluster_values[i])
                        b = '0-' + str(v_cluster_values[j])
                    elif i == 0 and j > 0 and j < len(v_cluster_values):
                        a = '0-' + str(e_cluster_values[i])
                        b = str(v_cluster_values[j-1]) + '-' + str(v_cluster_values[j])
                    elif i == 0 and j == len(v_cluster_values):
                        a = '0-' + str(e_cluster_values[i])
                        b = str(v_cluster_values[j-1]) + '-' + str(max(L_seconds))
                    elif j == 0 and i < len(e_cluster_values):
                        a = str(e_cluster_values[i-1]) + '-' + str(e_cluster_values[i])
                        b = '0-' + str(v_cluster_values[j])
                    elif j == 0 and i == len(e_cluster_values):
                        #a = str(e_cluster_values[i-1]) + '-' + str(max(S_arriving_times))
                        a = str(e_cluster_values[i - 1]) + '-' + str(24.0)
                        b = '0-' + str(v_cluster_values[j])
                    elif i < len(e_cluster_values) and j == len(v_cluster_values):
                        a = str(e_cluster_values[i-1]) + '-' + str(e_cluster_values[i])
                        b = str(v_cluster_values[j-1]) + '-' + str(max(L_seconds))
                    elif i == len(e_cluster_values) and j < len(v_cluster_values):
                        #a = str(e_cluster_values[i-1]) + '-' + str(max(S_arriving_times))
                        a = str(e_cluster_values[i - 1]) + '-' + str(24.0)
                        b = str(v_cluster_values[j-1]) + '-' + str(v_cluster_values[j])
                    elif i == len(e_cluster_values) and j == len(v_cluster_values):
                        #a = str(e_cluster_values[i-1]) + '-' + str(max(S_arriving_times))
                        a = str(e_cluster_values[i - 1]) + '-' + str(24.0)
                        b = str(v_cluster_values[j-1]) + '-' + str(max(L_seconds))
                    else:
                        a = str(e_cluster_values[i-1]) + '-' + str(e_cluster_values[i])
                        b = str(v_cluster_values[j-1]) + '-' + str(v_cluster_values[j])

                    if a not in cluster[key].keys():
                        cluster[key][a] = {}
                    if b not in cluster[key][a].keys():
                        cluster[key][a][b] = {}
                    cluster[key][a][b] = cluster_counter[i][j] / e_cluster_counter[i]
            #Visualisierung begonnen -> unwichtig für die Funktion
            '''
            cluster[key]['v_indices'] = v_cluster_indeces
            cluster[key]['v_values'] = v_cluster_values
            cluster[key]['ve_indices'] = e_cluster_indeces
            cluster[key]['ve_values'] = e_cluster_values
            cluster[key]['travel_time'] = travel_time[key]
            print("cluster " + str(cluster))
    
            #y-Werte müssen zunächst in Sekunden konvertiert werden
            ywerte = []
            #TODO: kann man defaultdict nach delta_times sortieren, sodass day_times entsprechend geordnet werden?
            for y in cluster[key]['travel_time']['delta_time']: #L_datetimes sind geordnete Timedeltas
                ywerte.append(y.total_seconds())
    
            # TODO: convert timestamps to datetime
            xwerte = [datetime(i) for i in cluster[key]['travel_time']['day_time']]
            plt.scatter(xwerte, ywerte)
            plt.xlabel("X-Werte")
            plt.ylabel("Y-Werte")
            plt.show()
            #TODO: zweites Diagramm: V-Clustering-farblich markieren
            # -> y-Werte sortieren und nacheinander plotten
            # neuer Plot: ist es möglich Punkte einzeln zu plotten und jeweils eine neue Farbe zu bestimmen?
            # ansonsten müssen die y-Werte geordnet werden und dabei die x-Werte in einem geimensamen neuen Array beigefügt werden
            for i in range(len(cluster[key]['v_values'])):
                ywerte = []
                xwerte = []
                for l in L_seconds: #L_datetimes sind geordnete Timedeltas
                    if l <= cluster[key]['v_values'][i]:
                        ywerte.append(l)
                        xwerte.append(cluster[key][])
    
            #TODO: drittes Diagramm: VE-Clustering-Wahrscheinlichkeiten bestimmen und Balkendiagramme
            # -> x-Werte sortieren und Wahrscheinlichkeiten innerhalb der Cluster bestimmen
    
            # TODO: visualize Clustering
            '''
        else: #falls nicht geclustert wird
            a = str(e_cluster_values[0])
            b = str(v_cluster_values[0])
            if a not in cluster[key].keys():
                cluster[key][a] = {}
            if b not in cluster[key][a].keys():
                cluster[key][a][b] = {}
            cluster[key][a][b] = 1
    print("cluster: " + str(cluster))