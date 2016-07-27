import os
import sys
import json

import pandas as pd
import numpy as np
from sklearn.metrics import silhouette_score as _silhouette_score

import graphs
from kshape import kshape, zscore, _sbd
import metadata

def silhouette_score(series, clusters):
    distances = np.zeros((series.shape[0], series.shape[0]))
    for idx_a, metric_a in enumerate(series):
        for idx_b, metric_b in enumerate(series):
            distances[idx_a, idx_b] = _sbd(metric_a, metric_b)[0]
    labels = np.zeros(series.shape[0])
    for i, (cluster, indicies) in enumerate(clusters):
        for index in indicies:
            labels[index] = i
    # silhouette is only defined, if we have 2 clusters with assignments at minimum
    if len(np.unique(labels)) == 1:
        return -1
    else:
        return _silhouette_score(distances, labels, metric='precomputed')

def do_kshape(name_prefix, df, cluster_size):
    columns = df.columns
    matrix = []
    for c in columns:
        matrix.append(zscore(df[c]))
    res = kshape(matrix, cluster_size)
    score = silhouette_score(np.array(matrix), res)
    for i, (centroid, assigned_series) in enumerate(res):
        d = {}
        for serie in assigned_series:
            d[columns[serie]] = pd.Series(matrix[serie], index=df.index)
        d["centroid"] = pd.Series(centroid, index=df.index)
        df2 = pd.DataFrame(d)
        figure = df2.plot()
        figure.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        name = "%s_%d" % (name_prefix, (i+1))
        print(name + ".tsv")
        df2.to_csv(name + ".tsv", sep="\t")
        graphs.write(df2, name + ".png")
    return score

def cluster_service(path, service, cluster_size):
    prefix = "%s/%s-cluster-%d" % (path, service["name"], cluster_size)
    if os.path.exists(prefix + "_1.png"):
        print("skip " + prefix)
        return
    filename = os.path.join(path, service["preprocessed_filename"])
    df = pd.read_csv(filename, sep="\t", index_col='time', parse_dates=True)
    score = do_kshape(prefix, df, cluster_size)
    if cluster_size < 2:
        # no silhouette_score for cluster size 1
        return
    print("silhouette_score: %f" % score)
    with metadata.update(path) as data:
        for srv in data["services"]:
            if srv["name"] == service["name"]:
                if "clusters" not in srv:
                    srv["clusters"] = {}
                srv["clusters"][cluster_size] = dict(silhouette_score=score)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write("USAGE: %s measurement\n" % argv[0])
        sys.exit(1)
    path = sys.argv[1]
    for n in range(2, 7):
        for srv in metadata.load(path)["services"]:
            cluster_service(path, srv, n)
