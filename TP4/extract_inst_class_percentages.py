from pathlib import Path
import re
BASE_PATH = Path(__file__).parent

paths = {
    "blowfish": BASE_PATH / "Projet/blowfish/m5out_blowfish/stats.txt",
    "dijkstra": BASE_PATH / "Projet/dijkstra/m5out_dijkstra/stats.txt",
}


def parse(path: str):
    text = Path(path).read_text()
    m = re.search(r"commitStats0\.numInsts\s+(\d+)", text)
    num_inst = int(m.group(1)) if m else None
    classes = {}
    for line in text.splitlines():
        if line.startswith("system.cpu.commitStats0.committedInstType::"):
            parts = line.split()
            name = parts[0].split("::", 1)[1]
            try:
                count = int(parts[1])
            except Exception:
                continue
            pct = None
            if len(parts) >= 3 and parts[2].endswith("%"):
                try:
                    pct = float(parts[2].rstrip("%"))
                except Exception:
                    pct = None
            classes[name] = (count, pct)
    return num_inst, classes


def main():
    for app, path in paths.items():
        num_inst, classes = parse(path)
        print(app, "numInsts", num_inst)
        items = [(k, v) for k, v in classes.items() if v[0] != 0 and k != "total"]
        items.sort(key=lambda kv: kv[1][0], reverse=True)
        for name, (count, pct) in items:
            if pct is None and num_inst:
                pct = count / num_inst * 100
            print(f"{name}\t{count}\t{pct:.2f}%")
        print("--")


if __name__ == "__main__":
    main()
