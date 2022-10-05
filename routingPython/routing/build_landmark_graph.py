"""
This class builds the landmark graph by counting the amount of times an edge is part of a taxi trajectory
and returning the k landmarks which appear most often.
"""
import os
import pandas as pd

def count_edges(dirPath_edge_id_lists):
    for file in os.listdir(dirPath_edge_id_lists):
        path = os.path.join(dirPath_edge_id_lists, file)
        df = pd.read_csv(path, names=['ID', 'DAY', 'TIME'], skiprows=[0], sep=" ", skipinitialspace=True)
        edge_count = {}
        for i, row in df.iterrows():
            edge_count[row['ID']] = edge_count.get(row['ID'], 0) + 1
    return edge_count

def get_k_landmarks(k, dirPath_edge_id_lists):
    edge_count = count_edges(dirPath_edge_id_lists)
    sorted_values = sorted(edge_count, key=edge_count.get, reverse=True)
    #print(sorted_values)
    k_landmarks = []
    for i in range(k):
        k_landmarks.append(int(sorted_values[i]))
    return k_landmarks

#def visualize_landmarks(k_landmarks)



