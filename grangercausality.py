import os
import sys
import json
import math
from collections import defaultdict
import itertools

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from scipy.stats.mstats import normaltest

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

def best_column_of_cluster(service_name, path, cluster_size):
    selected_columns = {}
    index = None
    for i in range(1, cluster_size + 1):
        best_distance = np.inf
        best_column = None
        cluster_path = os.path.join(path, "%s-cluster-%d_%d.tsv" % (service_name, cluster_size, i))
        df = pd.read_csv(cluster_path, sep="\t", index_col='time', parse_dates=True)
        for c in df.columns:
            if c == "centroid":
                continue
            distance = _sbd(df.centroid, df[c])[0]
            if distance < best_distance:
                best_distance = distance
                best_column = c
        if best_column != None:
            selected_columns[best_column] = df[best_column]
    return pd.DataFrame(data=selected_columns, index=df.index)

def read_service(srv, path):
    srv_path = os.path.join(path, srv["filename"])
    preferred = preferred_cluster(srv["clusters"])
    if preferred == 0:
        df = pd.read_csv(srv_path, sep="\t", index_col='time', parse_dates=True)
        df = df[srv["preprocessed_fields"]]
    else:
        df = best_column_of_cluster(srv["name"], path, preferred)

    new_names = []
    for column in df.columns:
        res = adfuller(df[column])
        if column.startswith(srv["name"]):
            new_names.append(column)
        else:
            new_names.append(srv["name"] + "-" + column)
    df.columns = new_names
    return df

def grangercausality(df, p_values, lags):
    c1 = df.columns[0]
    c2 = df.columns[1]
    try:
        res = grangercausalitytests(zscore(df), lags, verbose=False)
    except Exception as e:
        if df[c1].var() < 1e-30:
            print("low variance for %s, got: %s" % (c1, e))
        if df[c2].var() < 1e-30:
            print("low variance for %s, got: %s" % (c2, e))
        else:
            print("error while processing %s -> %s, got: %s" % (c1, c2, e))
        return
    p_values["perpetrator"].append(c1)
    p_values["consequence"].append(c2)
    for i in range(lags):
        lag = i + 1
        p_values["p_for_lag_%d" % lag].append(res[lag][0]['ssr_ftest'][1])

def combine(a, b):
    for x in a:
        for y in b:
            yield(x,y)

def _compare_services(srv_a, srv_b, path):
    df_a = read_service(srv_a, path)
    df_b = read_service(srv_b, path)
    p_values = defaultdict(list)
    df = pd.concat([df_a, df_b]).resample("500ms").mean()
    df.interpolate(method="time", limit_direction="both", inplace=True)
    df.fillna(method="bfill", inplace=True)

    _, pval = normaltest(df)

    for c1, c2 in combine(df_a.columns, df_b.columns):
        if c1 == c2:
            continue
        grangercausality(df[[c1, c2]], p_values, 5)
        grangercausality(df[[c2, c1]], p_values, 5)
    return pd.DataFrame(p_values)

def compare_services(srv_a, srv_b, path):
    print("%s -> %s" % (srv_a["name"], srv_b["name"]))
    causality_file = os.path.join(path, "%s-%s-causality-callgraph-2.tsv" % (srv_a["name"], srv_b["name"]))
    if os.path.exists(causality_file):
        print("skip %s" % causality_file)
        return
    df = _compare_services(srv_a, srv_b, path)
    #df.to_csv(causality_file, sep="\t")

def load_graph(callgraph_path):
    # TODO: replace with proper format (TGF), once I get my infrastruture
    callgraph = [
        ("web", "contacts"),
        ("web", "chat"),
        ("web", "doc-updater"),
        ("doc-updater", "mongodb"),
        ("track-changes", "redis"),
        ("chat", "mongodb"),
        ("real-time", "redis"),
        ("real-time", "doc-updater"),
        ("doc-updater", "web"),
        ("doc-updater", "track-changes"),
        ("docstore", "mongodb"),
        ("real-time", "web"),
        ("web", "tags"),
        ("web", "filestore"),
        ("haproxy", "web"),
        ("web", "redis"),
        ("chat", "web"),
        ("track-changes", "web"),
        ("web", "clsi"),
        ("web", "docstore"),
        ("clsi", "postgresql"),
        ("doc-updater", "redis"),
        ("web", "mongodb"),
        ("track-changes", "mongodb"),
        ("contacts", "mongodb"),
        ("haproxy", "real-time"),
        ("web", "spelling"),
    ]
    uniq = {}
    for a, b in callgraph:
        if a > b:
            a, b = b, a
        uniq[a + b] = (a, b)
    return uniq.values()

def find_causality(callgraph_path, metadata_path):
    data = metadata.load(metadata_path)
    call_pairs = load_graph(callgraph_path)
    services = {}
    for srv in data["services"]:
        services[srv["name"]] = srv
    for srv_a, srv_b in call_pairs:
        compare_services(services[srv_a], services[srv_b], metadata_path)
    #for srv_a, srv_b in itertools.product(data["services"], data["services"]):
    #    compare_services(srv_a, srv_b, metadata_path)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.stderr.write("USAGE: %s callgraph measurement\n" % sys.argv[0])
        sys.exit(1)
    find_causality(sys.argv[1], sys.argv[2])
