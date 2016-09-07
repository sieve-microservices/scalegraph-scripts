import sys
from collections import defaultdict
import argparse
import json

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

EXCLUDE=[]

def each_relation(tsv_paths):
    for path in tsv_paths:
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
            yield row_a, row_b

def write_json(json_file, paths, significance=0.05):
    edges = []
    for row_a, row_b in each_relation(paths):
        if (row_a.p_for_lag_1 <= significance and row_b.p_for_lag_1 <= significance) or \
           (row_a.p_for_lag_1 >  significance and row_b.p_for_lag_1 >  significance):
             # skip for the moment
             continue

        if row_b.p_for_lag_1 <= significance:
            row_a, row_b = row_b, row_a

        service_a, metric_a = row_a.perpetrator.split("-", 1)
        service_b, metric_b = row_a.consequence.split("-", 1)
        edges.append(dict(perpetrator_service=service_a,
            perpetrator_metric=metric_a,
            influenced_service=service_b,
            influenced_metric=metric_b,
            confidence=1 - row_a.p_for_lag_1))
    json.dump(edges, f, indent=4, sort_keys=True)

def write_dot(dot_file, paths, significance=0.05, include_insignificant=False):
    dot_file.write("""
digraph {
  overlap = false
  splines = true
""")
    for row_a, row_b in each_relation(paths):
        service_a, metric_a = row_a.perpetrator.split("-", 1)
        service_b, metric_b = row_a.consequence.split("-", 1)
        color = "black"
        if row_a.p_for_lag_1 <= significance and row_b.p_for_lag_1 <= significance:
             # skip for the moment
             #dir = "both"
             #symbol = "<->"
             continue
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

def parse_args():
    parser = argparse.ArgumentParser(prog='PROG', usage='%(prog)s [options]')
    parser.add_argument('--format', nargs="?", default="dot", choices=['json', 'dot'])
    parser.add_argument('--significance', type=float, default=0.05)
    parser.add_argument('output_file', help='graph file to write')
    parser.add_argument('causality_files', nargs="+", help="files with granger causality")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.format == "json":
        func = write_json
    else:
        func = write_dot

    with open(args.output_file, "w+") as f:
        print(args.output_file)
        func(f, args.causality_files, args.significance)
