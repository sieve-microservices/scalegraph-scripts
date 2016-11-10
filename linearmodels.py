import os
import sys
import re
import argparse
import json
from collections import defaultdict
from scipy.stats import linregress

import pandas as pd
import numpy as np
import multiprocessing as mp
from scipy.stats import linregress

import metadata
from plot import plt, sns
from preprocess import diff

def parse_args():
    parser = argparse.ArgumentParser(prog='slopes', usage='%(prog)s [options]')
    parser.add_argument('--output', help='path to tsv file with linear model', default="output.tsv.gz")
    parser.add_argument('--single-processing', help='path to csv file', action='store_true')
    parser.add_argument('services_metadata', help='json file with callgraph')
    parser.add_argument('measurements', nargs="+", help="measurement directories")
    return parser.parse_args()

def load_metadata(measurements):
    stats = defaultdict(list)
    for measurement in measurements:
        data = metadata.load(measurement)
        name = data["name"]
        m = re.match(r".*scale(?P<scale>\d+)", name)
        if m is None:
            sys.stderr.write("measurement %s does not contain scaling factor in its name" % measurement)
        scale = int(m.groupdict()["scale"])

        for srv in data["services"]:
            stats["name"].append(name)
            stats["service"].append(srv["name"])
            stats["scale"].append(scale)
            stats["filename"].append(os.path.join(measurement, srv["preprocessed_filename"]))
    return pd.DataFrame(stats)

def load_measurement(filename):
    return pd.read_csv(filename, sep="\t", index_col='time', parse_dates=True)

def _linearregression(m, service_a, service_b):
    stats = defaultdict(list)
    for scale in m.scale.unique():
        m_scale = m[m.scale == scale]
        for name in m_scale.name.unique():
            m_same = m_scale[m_scale.name == name]
            m_a = m_same[(m.service == service_a)]
            m_b = m_same[(m.service == service_b)]
            assert len(m_a) == 1 and len(m_b) == 1
            df_a = load_measurement(m_a.iloc[0].filename)
            df_b = load_measurement(m_b.iloc[0].filename)
            for metric_a in df_a.columns:
                for metric_b in df_b.columns:
                    series_a, series_b = df_a[metric_a].align(df_b[metric_b], join="inner")
                    assert len(series_a) > 0 and len(series_b) > 0
                    res = linregress(series_a, series_b)
                    res_a = linregress(series_a.index.astype("int64"), series_a)
                    res_b = linregress(series_b.index.astype("int64"), series_b)
                    stats["name"].append(name)
                    stats["metric_a"].append(metric_a)
                    stats["metric_b"].append(metric_b)
                    stats["service_a"].append(service_a)
                    stats["service_b"].append(service_b)
                    stats["scale"].append(scale)
                    stats["quotient"].append(res_a.slope / res_b.slope)
                    stats["slope_a"].append(res_a.slope)
                    stats["slope_b"].append(res_b.slope)
                    stats["p_value_a"].append(res_a[3])
                    stats["p_value_b"].append(res_b[3])
                    for i, type in enumerate(["slope", "intercept", "r_value", "p_value", "std_err"]):
                        stats[type].append(res[i])
    return stats

def process(args):
    return _linearregression(*args)

def linearregression_mp(measurements, callgraph):
    p = mp.Pool(24)
    results = p.map(process, [(measurements, a, b) for a, b in callgraph])
    p.close()
    p.join()
    stats = defaultdict(list)
    for result in results:
        for k, v in result.items():
            stats[k].extend(v)
    return pd.DataFrame(stats)

def linearregression(measurements, callgraph):
    for service_a, service_b in callgraph:
        _linearregression(measurements, service_a, service_b)
    return pd.DataFrame(stats)

def load_callgraph(metadata):
    with open(metadata) as f:
        data = json.load(f)
    graph = []
    for edges in data["callgraph"]["edges"]:
        graph.append((edges["from"], edges["to"]))
    return graph

def main():
    args = parse_args()
    callgraph = load_callgraph(args.services_metadata)
    if args.single_processing:
        func = linearregression
    else:
        func = linearregression_mp
    measurements = func(load_metadata(args.measurements), callgraph)
    measurements.to_csv(args.output, sep="\t", compression='gzip')
    #grouped = df.groupby([df.service, df.metric]).slope
    #metrics = grouped.filter(lambda x: x.count() >= 3)
    #describe = metrics.groupby([df.service, df.metric]).describe().unstack()
    #with open("report.html", "w+") as html:
    #    describe.transpose().to_html(html)

if __name__ == "__main__":
    main()
