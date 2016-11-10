from plot import plt, sns
import pandas as pd
import argparse
import numpy as np
from collections import defaultdict, OrderedDict
import metadata
import os
from sklearn import metrics
from igraph import split_join_distance

def load_cluster_assignments(measurements):
    all_measurements = defaultdict(list)
    for m in measurements:
        data = metadata.load(m)
        for srv in data["services"]:
            assignment = OrderedDict()
            selected = max(srv["clusters"], key=lambda x: srv["clusters"][x]['silhouette_score'])

            for k, c in srv["clusters"].items():
                all_clusters = []
                all_columns = []
                for idx, f in enumerate(c["filenames"]):
                    df = pd.read_csv(os.path.join(m, f), sep="\t")
                    columns = list(df.columns)
                    columns.remove("time")
                    columns.remove("centroid")
                    all_clusters.extend([idx] * len(columns))
                    all_columns.extend(columns)
                assignment = OrderedDict(sorted(zip(all_columns, all_clusters)))
                all_measurements["measurement"].append(m)
                all_measurements["service"].append(srv["name"])
                all_measurements["cluster_size"].append(int(k))
                all_measurements["assignment"].append(assignment)
                all_measurements["selected"].append(k == selected)
    return pd.DataFrame(all_measurements)

def distplot(df, column, filename):
    g = sns.FacetGrid(df, col="measurement_a", col_wrap=2, row_order=["1", "2", "3", "4", "5", "all"])
    g.map(sns.distplot, column, norm_hist=False, kde=False)
    g.set_titles("{col_name}")
    print(filename)
    plt.gcf().savefig(filename)

def main():
    args = parse_args()
    df = load_cluster_assignments(args.measurements)
    INFO_SCORE = "Mutual Information Score"
    SPLIT_JOIN_A = "Split-Join Index a"
    SPLIT_JOIN_B = "Split-Join Index b"
    scores = defaultdict(list)
    for pivot in df.measurement.unique():
        selected_cluster = df[(df.measurement == pivot) & (df.selected == True)]
        for _, a in selected_cluster.iterrows():
            other = df[(df.cluster_size == a.cluster_size) & (df.service == a.service) & (df.measurement != a.measurement)]
            for _, b in other.iterrows():
                diff = set(a.assignment.keys()).intersection(set(b.assignment.keys()))
                assignment_a = list([a.assignment[k] for k in sorted(diff)])
                assignment_b = list([b.assignment[k] for k in sorted(diff)])
                score = metrics.adjusted_mutual_info_score(assignment_a, assignment_b)
                dist_a, dist_b = split_join_distance(assignment_a, assignment_b)
                scores["service_a"].append(a.service)
                scores["measurement_a"].append(a.measurement[-1])
                scores["service_b"].append(a.service)
                scores["measurement_b"].append(b.measurement)
                scores[SPLIT_JOIN_A].append(dist_a)
                scores[SPLIT_JOIN_B].append(dist_b)
                scores[INFO_SCORE].append(score)
                scores["service_a"].append(a.service)
                scores["measurement_a"].append("all")
                scores["service_b"].append(a.service)
                scores["measurement_b"].append(b.measurement)
                scores[SPLIT_JOIN_A].append(dist_a)
                scores[SPLIT_JOIN_B].append(dist_b)
                scores[INFO_SCORE].append(score)

    scores_df = pd.DataFrame(scores)
    distplot(scores_df, INFO_SCORE, "mutual-information-score.png") 
    distplot(scores_df, SPLIT_JOIN_A, "split-join-index-a.png") 
    distplot(scores_df, SPLIT_JOIN_B, "split-join-index-b.png") 

def parse_args():
    parser = argparse.ArgumentParser(prog='graph', usage='%(prog)s [options]')
    parser.add_argument('measurements', nargs="+", help="benchmark data")
    return parser.parse_args()

if __name__ == "__main__":
    main()
