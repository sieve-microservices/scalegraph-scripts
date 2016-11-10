import os
import sys
import json
import math
from collections import defaultdict
import itertools
import re
import argparse
import fnmatch

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from scipy.stats import linregress

import metadata
from kshape import zscore, _sbd

from preprocess import interpolate_missing

def preferred_cluster(clusters):
    preferred = 0
    preferred_value = -1
    for k, v in clusters.items():
        if v["silhouette_score"] > preferred_value:
            preferred = int(k)
            preferred_value = v["silhouette_score"]
    return preferred

def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

def best_column_of_cluster(filenames, path):
    best_column_of_clusters = []
    index = None
    for filename in natural_sort(filenames):
        best_distance = np.inf
        best_column = None
        cluster_path = os.path.join(path, filename)
        df = pd.read_csv(cluster_path, sep="\t", index_col='time', parse_dates=True)
        for c in df.columns:
            if c == "centroid":
                continue
            distance = _sbd(df.centroid, df[c])[0]
            if distance < best_distance:
                best_distance = distance
                best_column = c
        best_column_of_clusters.append(best_column)
    return best_column_of_clusters

def read_service(srv, path):
    srv_path = os.path.join(path, srv["preprocessed_filename"])
    df = pd.read_csv(srv_path, sep="\t", index_col='time', parse_dates=True)
    for c in df.columns:
        df[c] = zscore(df[c])

    preferred = preferred_cluster(srv["clusters"])
    cluster = srv["clusters"][str(preferred)]
    selected_metrics = best_column_of_cluster(cluster["filenames"], path)
    with metadata.update(path) as data:
        for s in data["services"]:
            if s["name"] == srv["name"]:
                s["clusters"][str(preferred)]["grangercausality-metrics"] = selected_metrics

    return Service(srv["name"], selected_metrics, df)

def grangercausality(service_a, service_b, df, stats, lags):
    c1 = df.columns[0]
    c2 = df.columns[1]
    try:
        res = grangercausalitytests(df, lags, verbose=False)
    except Exception as e:
        if df[c1].var() < 1e-30:
            print("low variance for %s, got: %s" % (c1, e))
        if df[c2].var() < 1e-30:
            print("low variance for %s, got: %s" % (c2, e))
        else:
            print("error while processing %s -> %s, got: %s" % (c1, c2, e))
        return
    reg = linregress(df[c1], df[c2])
    reg_a = linregress(df[c1].index.astype("int64"), df[c1])
    reg_b = linregress(df[c2].index.astype("int64"), df[c2])

    stats["perpetrator_service"].append(service_a.name)
    stats["perpetrator_metric"].append(c1)
    stats["consequence_service"].append(service_b.name)
    stats["consequence_metric"].append(c2)
    stats["selected_by_clustering"].append(c1 in service_a.selected_metrics and c2 in service_b.selected_metrics)
    stats["quotient"].append(reg_a.slope / reg_b.slope)
    stats["slope_a"].append(reg_a.slope)
    stats["slope_b"].append(reg_b.slope)
    stats["p_value_a"].append(reg_a[3])
    stats["p_value_b"].append(reg_b[3])

    for i, type in enumerate(["slope", "intercept", "r_value", "p_value", "std_err"]):
        stats[type].append(reg[i])

    for i in range(lags):
        lag = i + 1
        stats["p_for_lag_%d" % lag].append(res[lag][0]['ssr_ftest'][1])

def combine(a, b):
    for x in a:
        for y in b:
            yield(x,y)

class Service():
    def __init__(self, name, selected_metrics, df):
        self.name = name
        self.selected_metrics = set(selected_metrics)
        self.df = df

def _compare_services(service_a, service_b, path, sampling_rate):
    stats = defaultdict(list)
    df = interpolate_missing(pd.concat([service_a.df, service_b.df]), sampling_rate)

    for c1, c2 in combine(service_a.df.columns, service_b.df.columns):
        if c1 == c2:
            continue
        grangercausality(service_a, service_b, df[[c1, c2]], stats, 5)
        grangercausality(service_b, service_a, df[[c2, c1]], stats, 5)
    return pd.DataFrame(stats)

#def read_slas_metrics(service_sla, path):
#    for file, metrics in service_sla.items():
#        metric_path = os.path.join(path, file)
#        import pdb; pdb.set_trace()

def compare_services(srv_a, srv_b, path, sampling_rate, slas=None):
    print("%s -> %s" % (srv_a["name"], srv_b["name"]))
    causality_file = os.path.join(path, "%s-%s-causality-callgraph-best.tsv.gz" % (srv_a["name"], srv_b["name"]))
    if os.path.exists(causality_file):
        print("skip %s" % causality_file)
        return

    service_a = read_service(srv_a, path)
    service_b = read_service(srv_b, path)

    #if slas is not None:
    #    slas_a = read_slas_metrics(slas[srv_a["name"]], path)
    #    slas_b = read_slas_metrics(slas[srv_b["name"]], path)
    #    df1 = _compare_services(srv_a["name"], df_a, srv_b["name"], slas_b, path, sampling_rate)
    #    df2 = _compare_services(srv_a["name"], slas_a, srv_b["name"], df_b, path, sampling_rate)
    #else:

    df = _compare_services(service_a, service_b, path, sampling_rate)
    df.to_csv(causality_file, sep="\t", compression="gzip")

def undirected_callgraph(callgraph):
    uniq = {}
    for edge in callgraph:
        a = edge["from"]
        b = edge["to"]
        if a > b:
            a, b = b, a
        uniq[a + b] = (a, b)
    return uniq.values()

def match_field(service_name, field, sla_metrics):
    for assigned_srv, patterns in sla_metrics["services"].items():
        for wildcard in patterns["wildcards"]:
            if fnmatch.fnmatch(field, wildcard):
                return assigned_srv
    for wildcard in sla_metrics["generic"]["wildcards"]:
        if fnmatch.fnmatch(field, wildcard):
            return service_name

def assign_slas(sla_metrics, measurement_data):
    services = defaultdict(lambda: defaultdict(list))
    for srv in measurement_data["services"]:
        preprocessed_filename = srv["preprocessed_filename"]
        for field in srv["preprocessed_fields"]:
            service_name = match_field(srv["name"], field, sla_metrics)
            if service_name is not None:
                services[service_name][preprocessed_filename].append(field)
    import pdb; pdb.set_trace()
    return services


def find_causality(path, services_data, args):
    measurement_data = metadata.load(path)
    call_pairs = undirected_callgraph(services_data["edges"])

    services = {}
    for srv in measurement_data["services"]:
        services[srv["name"]] = srv
    if args.compare_slas:
        slas = assign_slas(services_data["sla_metrics"], measurement_data)
    else:
        slas = None

    if args.parallel:
        from submit_jobs import lview
        def _compare_services(args):
            import grangercausality
            from imp import reload
            reload(grangercausality)
            grangercausality.compare_services(*args)

        ids = []
        for srv_a, srv_b in call_pairs:
            lview.block = True
            res = lview.apply_async(_compare_services, (services[srv_a], services[srv_b], path, args.sampling_rate, slas))
            ids.extend(res.msg_ids)
        return ids
    else:
        for srv_a, srv_b in call_pairs:
            compare_services(services[srv_a], services[srv_b], path, args.sampling_rate, slas)


def parse_args():
    parser = argparse.ArgumentParser(prog='grangercausality', usage='%(prog)s [options]')
    parser.add_argument('services_metadata', help='json file with callgraph and sla_metrics')
    parser.add_argument('measurement_directories', nargs="+", help="measurement directories")
    parser.add_argument('--compare-slas', action='store_true', help="compare metrics with slas")
    parser.add_argument('--sampling-rate', default=(1/2), help="how often data is updated per second")
    parser.add_argument('--parallel', action='store_true', help="submit job to ipython parallel cluster")
    return parser.parse_args()


def main():
    args = parse_args()
    ids = []
    for path in args.measurement_directories:
        if not os.path.exists(os.path.join(path, "metadata.json")):
            sys.stderr.write("skip '%s': cannot find metadata.json\n" % path)
            continue
        services_data = json.load(open(args.services_metadata))
        if args.parallel:
            ids.extend(find_causality(path, services_data, args))
        else:
            find_causality(path, services_data, args)

    if args.parallel:
        from submit_jobs import lview
        lview.get_result(ids, owner=False).wait_interactive()

if __name__ == '__main__':
    main()
