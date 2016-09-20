import os
import argparse
from collections import defaultdict

import pandas as pd
import numpy as np
from scipy.stats import linregress

import metadata
from plot import plt, sns
from preprocess import diff

def parse_args():
    parser = argparse.ArgumentParser(prog='slopes', usage='%(prog)s [options]')
    parser.add_argument('graph', help="distribution graph file name")
    parser.add_argument('measurements', nargs="+", help="measurement directories")
    return parser.parse_args()

def timeregression(measurements):
    stats = defaultdict(list)
    for measurement in measurements:
        data = metadata.load(measurement)
        for srv in data["services"]:
            filename = os.path.join(measurement, srv["preprocessed_filename"])
            df = pd.read_csv(filename, sep="\t", index_col='time', parse_dates=True)
            for c in df.columns:
                column = df[c]
                res = linregress(column.index.astype("int64"), column)
                stats["name"].append(os.path.basename(measurement))
                stats["service"].append(srv["name"])
                stats["metric"].append(c)
                for i, type in enumerate(["slope", "intercept", "r_value", "p_value", "std_err"]):
                    stats[type].append(res[i])

    return pd.DataFrame(stats)

def main():
    args = parse_args()
    df = timeregression(args.measurements)
    grouped = df.groupby([df.service, df.metric]).slope
    metrics = grouped.filter(lambda x: x.count() >= 3)
    describe = metrics.groupby([df.service, df.metric]).describe().unstack()
    with open("report.html", "w+") as html:
        describe.transpose().to_html(html)

if __name__ == "__main__":
    main()
