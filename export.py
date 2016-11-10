import os
import sys
import re
import numpy as np
import metadata
import pandas as pd
from kshape import _sbd

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
    selected_columns = {}
    best_column_of_clusters = []
    other_columns = []
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
        if best_column != None:
            selected_columns[best_column] = df[best_column]
        best_column_of_clusters.append(best_column)
        other_columns.append(df.columns)
    return best_column_of_clusters, other_columns

if __name__ == "__main__":
    for path in sys.argv[1:]:
        data = metadata.load(path)
        edge = []
        name = []
        is_diff = []
        has_absolute = []
        services = []
        for srv in data["services"]:
            if srv["name"] == "loadgenerator": continue
            preferred = preferred_cluster(srv["clusters"])
            cluster = srv["clusters"][str(preferred)]
            selected_metrics, other_columns = best_column_of_cluster(cluster["filenames"], path)
            for i, metric in enumerate(selected_metrics):
                if metric is None: continue
                for other_column in other_columns[i]:
                    if other_column == "centroid" or other_column == metric: continue
                    services.append(srv["name"])
                    edge.append(metric.strip("-diff"))
                    name.append(other_column.strip("-diff"))
                    is_diff.append(other_column.endswith("-diff"))
                    has_absolute.append("uptime_in_seconds" not in other_column)
        columns = dict(selected_metric=edge, other_metric_in_cluster=name, is_diff=is_diff, has_absolute=has_absolute)
        df = pd.DataFrame(columns, columns =  ["selected_metric", "other_metric_in_cluster", "is_diff", "has_absolute"])
        path = os.path.join(os.path.basename(path) + ".tsv")
        print(path)
        df.to_csv(path, sep="\t", index=False)
