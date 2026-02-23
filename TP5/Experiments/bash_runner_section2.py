import subprocess


GEM5 = "/home/g/gbusnot/ES201/tools/TP5/gem5-stable"
threads_list = [1,2, 4, 8, 16, 32, 64]
taille_matrice = 64

def run_bash(commande) -> dict:
    resultat = subprocess.run(commande, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    return {
        "stdout": resultat.stdout,
        "stderr": resultat.stderr,
        "returncode": resultat.returncode
    }

def parse_stats(stats_file):
    resultats = {}
    with open(stats_file, "r") as f:
        for ligne in f:
            if "numCycles" in ligne and "cpu" in ligne:
                parties = ligne.split()
                resultats[parties[0]] = int(parties[1])
            if ligne.strip().startswith("sim_insts ") and "sim_insts" not in resultats:
                parties = ligne.split()
                resultats["sim_insts"] = int(parties[1])
    return resultats

if __name__ == "__main__":
    numAppCycles = []
    speedUp = []
    ipc_list = []

    # Fichier de résultats
    with open("resultats.txt", "w") as fichier_resultats:
        fichier_resultats.write("threads,cycles_max,cpu_max,speedup,ipc_max\n")

        for n in threads_list:
            commande = f"{GEM5}/build/ARM/gem5.fast {GEM5}/configs/example/se.py -n {n} -c {GEM5}/../test_omp -o '{n} {taille_matrice}'"
            run_bash(commande)

            resultats = parse_stats("m5out/stats.txt")
            print(f"\n=== {n} threads ===")

            # Filtrer uniquement les cycles CPU
            cycles = {k: v for k, v in resultats.items() if "numCycles" in k}
            for cpu, val in cycles.items():
                print(f"  {cpu} : {val}")

            # CPU avec le plus de cycles
            cpu_max = max(cycles, key=cycles.get)
            valeur_max = cycles[cpu_max]
            print(f"  CPU max : {cpu_max} ({valeur_max} cycles)")
            numAppCycles.append(valeur_max)

            # Speedup
            if speedUp == []:
                speedUp.append(1.0)
            else:
                speedUp.append(numAppCycles[0] / valeur_max)
            print(f"  Speedup : {speedUp[-1]:.3f}")

            # IPC max
            ipc_max = resultats["sim_insts"] / resultats[cpu_max]
            ipc_list.append(ipc_max)
            print(f"  IPC max : {ipc_max:.3f}")

            # Sauvegarde dans le fichier
            fichier_resultats.write(f"{n},{valeur_max},{cpu_max},{speedUp[-1]:.3f},{ipc_max:.3f}\n")

    print("\nRésultats sauvegardés dans resultats.txt")

"""
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

    """