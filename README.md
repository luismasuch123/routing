# T-Drive algorithm
***
The IVMM algorithm finds the fastest route in a given road network by taking into account a large number of taxi trajectories. It is assumed that taxi drivers are experienced and can therefore find the best routes dependent on the time of day.
**Author: Luis Masuch Ibanez**    
**Created: 15/06/2022**  

#Main Contributions
***
I have implemented the T-Drive algorithm. The algorithm doesn't consider the need of rematching the resulting landmarks with the time they were visited, which is necessary to estimate the travel times between landmarks. I try to deal with that issue.

#Anmerkungen 
Aktuell build_landmark_graph fertig implementiert. Die restlichen Schritte noch nicht.
***
Bei der travel_time estimation bestehen mehrere Probleme. Zum einen müssen für alle Paare von landmarks, in jedem GPS-Log, in dem beide landmarks vorkommen, die GPS-Koordinaten mit den Zeitpunkten gematched werden, zu denen die landmarks befahren wurden.
Dabei können nicht einfach die GPS-Punkte mit der geringsten Distanz zu den landmarks gewählt werden, da die landmarks auf Basis von mehreren nahegelegenen GPS-Punkten gesetzt/abgestimmt wurden. Eine landmark ist demnach mehreren GPS-Punkten zugehörig. Diese Richtungsabhängigkeit muss berücksichtigt werden, da ansonsten eine landmark einem GPS-Punkt zugeordnet werden könnte, welcher zwar am nächsten an der landmark liegt, aber erst zu einem späteren/früheren Zeitpunkt befahren wurde und gar nicht zur landmark beiträgt.
Zum anderen muss auch berücksichtigt werden, dass landmarks mehrmals innerhalb eines GPS-Logs auftauchen können.
Möglicherweise könnte man bereits beim map matching, die resultierenden edges mit Zeitpunkten versehen. Daraus würden weniger Fehler beim "re-matching" resultieren bzw. wäre dies dann nicht mehr notwendig.
***
Das rough routing, sowie das refined routing müssen noch implementiert werden. Für die schnellsten Routen zwischen den landmarks könnte A* oder Dijkstraa angewendet werden. Das refined routing wird mithilfe von dynamischer Optimierung durchgeführt.