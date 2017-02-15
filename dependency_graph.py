import sys
import os
from collections import defaultdict, OrderedDict
import argparse
import json
import glob

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

EXCLUDE = []

def each_relation(paths):
    for path in paths:
        for tsv in sorted(glob.glob(os.path.join(path, "*-causality-callgraph-best.tsv.gz"))):
            df = pd.read_csv(tsv, sep="\t")
            if len(df) == 0:
                continue
            # bug in causation!
            rows = df.iterrows()
            while True:
                try:
                    row_a = next(rows)[1]
                    row_b = next(rows)[1]
                except StopIteration:
                    break
                yield os.path.basename(path), row_a, row_b

def collect_relations(paths, significance=0.05):
    edges = defaultdict(list)
    s = {}
    i = 0
    for measurement, row_a, row_b in each_relation(paths):
        if (row_a.p_for_lag_1 <= significance and row_b.p_for_lag_1 <= significance) or \
           (row_a.p_for_lag_1 >  significance and row_b.p_for_lag_1 >  significance):
             # skip for the moment
             continue

        if row_b.p_for_lag_1 <= significance:
            row = row_b
        else:
            row = row_a
        edges["measurement"].append(measurement)
        edges["perpetrator_service"].append(row.perpetrator_service)
        edges["perpetrator_metric"].append(row.perpetrator_metric)
        edges["consequence_service"].append(row.consequence_service)
        edges["consequence_metric"].append(row.consequence_metric)
        edges["regression_confidence"].append((1 - row.p_value))
        edges["regression_quotient"].append(row.quotient)
        edges["regression_slope"].append(row.slope)
        edges["selected_by_clustering"].append(row.selected_by_clustering)
        edges["causality_confidence"].append(1 - row.p_for_lag_1)
    return pd.DataFrame(edges)

def write_json(json_file, paths, significance=0.10):
    collect_relations(paths, significance).to_json(json_file, orient="records")

def relative_value(column_x, column_y):
    return lambda x: ", ".join(map(lambda val: str(100 * (val / x[column_x])), x[column_y]))

def std(column_x, column_y):
    return lambda x: np.std([x[column_x]] + list(x[column_y]))

def average(column_x, column_y):
    return lambda x: np.average([x[column_x]] + list(x[column_y]))

ALIASES = OrderedDict([
    ("measurement_x", "Measurement"),
    ("perpetrator_service", "Perpetrator Service"),
    ("perpetrator_metric", "Perpetrator Metric"),
    ("consequence_service", "Consequence Service"),
    ("consequence_metric", "Consequence Metric"),
    ("regression_quotient_x", "Quotient"),
    ("relative_regression_quotient_y", "Relative Quotient Of Other M. [%]"),
    ("std_regression_quotient", "Std(All Quotients)"),
    ("avg_regression_quotient", "Average(All Quotients)"),
    ("regression_slope_x", "Slope"),
    ("relative_regression_slope_y", "Relative Slope Of Other M. [%]"),
    ("std_regression_slope", "Std(All Slopes)"),
    ("avg_regression_slope", "Average(All Slopes)")
])

def write_table(json_file, paths, significance=0.05):
    df = collect_relations(paths, significance)
    measurements = df.measurement.unique()
    for measurement in measurements:
        selected = df[(df.measurement == measurement) & df.selected_by_clustering]
        other_runs = df[df.measurement != measurement]
        join_key = ["perpetrator_service", "perpetrator_metric", "consequence_service", "consequence_metric"]
        merge = selected.merge(other_runs, on=join_key, how='left')
        join_key2 = join_key + ["measurement_x"]
        aggregations = {}
        for k in merge.columns.difference(set(join_key2)):
            if k.endswith("_x"):
                aggregations[k] = lambda x: x.iloc[0]
            else:
                aggregations[k] = lambda x: tuple(x)
        result = merge.groupby(join_key2).agg(aggregations).reset_index()

        result["relative_regression_quotient_y"] = result.apply(relative_value("regression_quotient_x", "regression_quotient_y"), axis=1)
        result["std_regression_quotient"] = result.apply(std("regression_quotient_x", "regression_quotient_y"), axis=1)
        result["avg_regression_quotient"] = result.apply(average("regression_quotient_x", "regression_quotient_y"), axis=1)
        result["relative_regression_slope_y"] = result.apply(relative_value("regression_slope_x", "regression_slope_y"), axis=1)
        result["std_regression_slope"] = result.apply(std("regression_slope_x", "regression_slope_y"), axis=1)
        result["avg_regression_slope"] = result.apply(average("regression_slope_x", "regression_slope_y"), axis=1)

        result = result.sort_values(by=["perpetrator_service", "perpetrator_metric", "consequence_service", "consequence_metric"])
        pd.set_option('display.max_colwidth', -1)
        basename = measurement + ("-confidence-%.02f%%" % significance) 
        dot_path = basename + ".dot"
        with open(dot_path, "w+") as f:
            print(dot_path)
            write_dot2(f, result)

        result = result.rename(columns=ALIASES)
        html_path = basename + ".html"
        with open(html_path, "w+") as f:
            print(html_path)
            result.to_html(f, columns = ALIASES.values())
            for field in ["std_regression_quotient", "avg_regression_quotient", "std_regression_slope", "avg_regression_slope"]:
                f.write("<pre>%s</pre>" % result[ALIASES[field]].describe())

def write_dot2(dot_file, df):
    dot_file.write("""
digraph {
  overlap = false
  splines = true
""")
    for _, r in df.iterrows():
        args = (r.perpetrator_service,
                r.consequence_service,
                r.perpetrator_metric,
                r.consequence_metric,
                r.causality_confidence_x,
                r.regression_confidence_x,
                r.regression_quotient_x,
                r.regression_slope_x)
        dot_file.write('  "%s" -> "%s" [tooltip="%s -> %s (granger-causality (p-value): %f,' 'regression (p-value): %f, quotient: %f, slope: %f)",dir=forward,color=black]\n' % args)
    dot_file.write("}")

def write_dot(dot_file, paths, significance=0.10, include_insignificant=False):
    dot_file.write("""
digraph {
  overlap = false
  splines = true
""")
    for _, row_a, row_b in each_relation(paths):
        service_a, metric_a = row_a.perpetrator_service, row_a.perpetrator_metric
        service_b, metric_b = row_a.consequence_service, row_a.consequence_metric
        color = "black"
        if row_a.p_for_lag_1 <= significance and row_b.p_for_lag_1 <= significance:
             # skip for the moment
             #dir = "both"
             #symbol = "<->"
             continue
        elif row_a.p_for_lag_1 <= significance:
            dir = "forward"
            symbol = "->"
            quotient = row_b.quotient
            slope = row_b.slope
            regression = row_b.p_value
        elif row_b.p_for_lag_1 <= significance:
            dir = "back"
            symbol = "<-"
            quotient = row_a.quotient
            slope = row_a.quotient
            regression = row_a.p_value
        elif include_insignificant:
            dir = "both"
            symbol = "<->"
            color = "red"
        else:
            continue
        weight = 1 - min(row_a.p_for_lag_1, row_b.p_for_lag_1)
        args = (service_a, service_b, row_a.perpetrator_metric, symbol, row_a.consequence_metric, weight, regression, quotient, slope, weight, dir, color)
        dot_file.write('  "%s" -> "%s" [tooltip="%s %s %s (granger-causality (p-value): %f, regression (p-value): %f, quotient: %f, slope: %f)",penwidth=%.3f,dir=%s,color=%s]\n' % args)
    dot_file.write("}")

def parse_args():
    parser = argparse.ArgumentParser(prog='PROG', usage='%(prog)s [options]')
    parser.add_argument('--format', nargs="?", default="dot", choices=['json', 'dot', 'table'])
    parser.add_argument('--significance', type=float, default=0.10)
    parser.add_argument('output_file', help='graph file to write')
    parser.add_argument('measurements', nargs="+", help="measurement directory with granger causality files")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.format == "json":
        func = write_json
    elif args.format == "table":
        func = write_table
    else:
        func = write_dot

    with open(args.output_file, "w+") as f:
        print(args.output_file)
        for i in [0.01, 0.05, 0.10]:
            func(f, args.measurements, i)
