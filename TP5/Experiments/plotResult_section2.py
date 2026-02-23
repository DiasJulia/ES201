import csv
import matplotlib.pyplot as plt

threads_list = []
numAppCycles = []
speedUp = []
ipc_list = []

with open("resultats.txt", "r") as f:
    reader = csv.DictReader(f)  # lit la première ligne comme en-têtes
    for ligne in reader:
        threads_list.append(int(ligne["threads"]))
        numAppCycles.append(int(ligne["cycles_max"]))
        speedUp.append(float(ligne["speedup"]))
        ipc_list.append(float(ligne["ipc_max"]))

print("threads :", threads_list)
print("cycles  :", numAppCycles)
print("speedup :", speedUp)
print("ipc     :", ipc_list)

# Graphe cycles
plt.figure()
plt.plot(threads_list, numAppCycles, marker='o', label="Nb cycles application")
plt.xlabel("Nombre de threads")
plt.ylabel("Nombre de cycles (cpu max)")
plt.title("Cycles d'exécution en fonction du nombre de threads")
plt.legend()
plt.grid(True)
plt.savefig("cycles.png")
plt.show()

# Graphe speedup
plt.figure()
plt.plot(threads_list, speedUp, marker='o', label="Speedup réel")
plt.plot(threads_list, [float(n) for n in threads_list], linestyle='--', label="Speedup idéal")
plt.xlabel("Nombre de threads")
plt.ylabel("Speedup")
plt.title("Speedup en fonction du nombre de threads")
plt.legend()
plt.grid(True)
plt.savefig("speedup.png")
plt.show()

# Graphe IPC
plt.figure()
plt.plot(threads_list, ipc_list, marker='o', label="IPC max")
plt.xlabel("Nombre de threads")
plt.ylabel("IPC")
plt.title("IPC max en fonction du nombre de threads")
plt.legend()
plt.grid(True)
plt.savefig("ipc.png")
plt.show()