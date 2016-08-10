import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

EXCLUDE=[]

def write_dot(dot_file, paths, significance=0.01, include_insignificant=False):
    dot_file.write("""
digraph {
  overlap = false
  splines = true
""")

    for path in paths:
        df = pd.read_csv(path, sep="\t")
        if len(df) == 0:
            continue
        # bug in causation!
        df.drop_duplicates(subset=["perpetrator", "consequence"], inplace=True)
        rows = df.iterrows()
        while True:
            try:
                row_a = next(rows)[1]
                row_b = next(rows)[1]
            except StopIteration:
                break
            service_a, metric_a = row_a.perpetrator.split("-", 1)
            service_b, metric_b = row_a.consequence.split("-", 1)
            if service_a in EXCLUDE or service_b in EXCLUDE:
                continue
            color = "black"
            if row_a.p_for_lag_1 <= significance and row_b.p_for_lag_1 <= significance:
                continue
                dir = "both"
                symbol = "<->"
            elif row_a.p_for_lag_1 <= significance:
                dir = "forward"
                symbol = "->"
            elif row_b.p_for_lag_1 <= significance:
                dir = "back"
                symbol = "<-"
            elif include_insignificant:
                dir = "both"
                symbol = "<->"
                color = "red"
            else:
                continue
            weight = 1 - min(row_a.p_for_lag_1, row_b.p_for_lag_1)
            args = (service_a, service_b, row_a.perpetrator, symbol, row_a.consequence, weight, weight, dir, color)
            dot_file.write('  "%s" -> "%s" [tooltip="%s %s %s (%f)",penwidth=%.3f,dir=%s,color=%s]\n' % args)

    dot_file.write("}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("USAGE: %s dot_path causality_files...\n" % sys.argv[0])
        sys.exit(1)
    with open(sys.argv[1], "w+") as f:
        write_dot(f, sys.argv[2:])
