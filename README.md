# T-Drive algorithm
***
The IVMM algorithm finds the fastest route in a given road network by taking into account a large number of taxi trajectories. It is assumed that taxi drivers are experienced and can therefore find the best routes dependent on the time of day.
**Author: Luis Masuch Ibanez**    
**Created: 15/06/2022**  

#Main Contributions
***
I have implemented the T-Drive algorithm. The algorithm doesn't consider the need of rematching the resulting landmarks with the time they were visited, which is necessary to estimate the travel times between landmarks. I try to deal with that issue.

#Anmerkungen 
Aktuell ist build_landmark_graph fertig implementiert. Die travel_time_estimation ist beinahe fertig. Die restlichen Schritte noch nicht.
***
Um die travel_time_estimation zu vereinfachen werden bereits die edges, die aus dem map-matching resultieren, direkt mit den Zeitpunkten verknüpft. Ansonsten müsste man die edges mit den GPS-Logs rematchen.
***
Beim Clustering für die travel_time_estimation werden tresholds gesetzt, bei deren Unterschreitung nicht weiter geclustert wird. Aus dem Paper ist nicht ersichtlich, wie die tresholds gesetzt werden soll. Aktuell sind sie auf 0.5 gesetzt. In estimate_travel_times besteht die Möglichkeit die Anzahl der Cluster zu begrenzen (aktuell: set_cluster_limit = True). Dabei können sowohl das V-Clustering, als auch das E-Clustering manuell begrenzt werden.
Das rough routing, sowie das refined routing müssen noch implementiert werden. Für die schnellsten Routen zwischen den landmarks könnte A* oder Dijkstraa angewendet werden. Das refined routing wird mithilfe von dynamischer Optimierung durchgeführt.
Aktuell existiert noch keine Graphen-Struktur, welche die landmarks sowie deren Kanten widerspiegelt. Der Graph kann auf Basis der gefundenen landmarks und dem Cluster bestimmt werden, in dem die Sobald ein Graph erstellt wurde, kann das rough routing durchgeführt werden. (mit rtree.nearest_point() könnte gegebenenfalls die nächste landmark von Start- oder Zielpunkt der Anfrage ausgehend bestimmt werden, um das rough routing durchzuführen)
***
Falls zwischen zwei landmarks nur eine einzige Tour durchgeführt wurde, ist im Cluster kein Intervall angegeben, sondern der Datenpunkt.
***
Test.py ist die main-Methode, in welcher die landmarks aus den edge_id_lists (Kanten, welche das Ergebnis des map-matchings sind) gefunden werden und anschließend die Zeiten zwischen zwei landmarks durch die travel_time_estimation() bestimmt werden.