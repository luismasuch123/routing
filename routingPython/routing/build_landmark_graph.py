import os
import pandas as pd

#Feld oder doch lieber Set dass über edge-Nummer angesprochen wird, sodass landmarks einfach durch Sortierung nach größten Werten sortiert werden

def count_edges(dirPath_edge_id_lists):
    for file in os.listdir(dirPath_edge_id_lists):
        path = os.path.join(dirPath_edge_id_lists, file)
        df = pd.read_csv(path, names=['edge'], skiprows=[0])
        edge_count = {}
        for i, row in df.iterrows():
            edge_count[row['edge']] = edge_count.get(row['edge'], 0) + 1
    return edge_count

def get_k_landmarks(k, dirPath_edge_id_lists):
    edge_count = count_edges(dirPath_edge_id_lists)
    sorted_values = sorted(edge_count, key=edge_count.get, reverse=True)
    print(sorted_values)
    k_landmarks = []
    for i in range(k):
        k_landmarks.append(sorted_values[i])
    return k_landmarks

#def visualize_landmarks(k_landmarks)



