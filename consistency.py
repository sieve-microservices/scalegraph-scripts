from plot import plt, sns
import pandas as pd
import argparse
import numpy as np
from collections import defaultdict, OrderedDict
import metadata
import os
from sklearn import metrics
#from igraph import split_join_distance

FONT_SIZE=25
plt.rcParams.update({
    "font.size": FONT_SIZE,
    "axes.labelsize" : FONT_SIZE,
    "font.size" : FONT_SIZE,
    "text.fontsize" : FONT_SIZE,
    "legend.fontsize": FONT_SIZE,
    "xtick.labelsize" : FONT_SIZE * 0.8,
    "ytick.labelsize" : FONT_SIZE * 0.8,
    })

def load_cluster_assignments(measurements):
    all_measurements = defaultdict(list)
    for m in measurements:
        data = metadata.load(m)
        for srv in data["services"]:
            if srv["name"] == "loadgenerator": continue
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
    SERVICES="Services"
    INFO_SCORE = "AMI"
    SPLIT_JOIN_A = "Split-Join Index a"
    SPLIT_JOIN_B = "Split-Join Index b"

    measurements = df.measurement.unique()
    df2 = df[df.measurement.isin(measurements) & df.selected]

    df3 = df2.merge(df2, on=["service"], how="inner")
    df4 = df3[df3.measurement_x != df3.measurement_y]
    df4["unique"] = df4.apply(lambda row: ", ".join(sorted([row.service, row.measurement_x, row.measurement_y])), axis=1)
    df5 = df4.drop_duplicates(["unique"])

    scores = []
    for _, row in df5.iterrows():
        diff = set(row.assignment_x.keys()).intersection(set(row.assignment_y.keys()))
        assignment_x = list([row.assignment_x[k] for k in sorted(diff)])
        assignment_y = list([row.assignment_y[k] for k in sorted(diff)])
        scores.append(metrics.adjusted_mutual_info_score(assignment_x, assignment_y))
    df5[INFO_SCORE] = scores

    sns.set(font_scale=1.3)
    sns.set_style("whitegrid")
    for _, combinations in df5.drop_duplicates(["measurement_x", "measurement_y"]).iterrows():
        x, y = combinations.measurement_x, combinations.measurement_y
        df6 = df5[(df5.measurement_x == x) & (df5.measurement_y == y)]
        df6 = df6[(df6.service != "postgresql") &
                  (df6.service != "filestore") &
                  (df6.service != "mongodb")]
        df6 = df6.rename(columns={"service": SERVICES})
        g = sns.factorplot(x=SERVICES,
                           y=INFO_SCORE,
                           data=df6,
                           kind="bar",
                           palette=sns.color_palette(palette="gray", n_colors=6, desat=0.5))
        g.despine(left=True)
        g.set_xticklabels(rotation=65, ha="right")
        plt.subplots_adjust(bottom=0.35, top=0.85)

        filename = "mutual-information-score-%s-%s.pdf"  % (x[-1], y[-1])
        g.fig.suptitle("AMI between\nmeasurement %s and %s" % (x[-1], y[-1]))
        print(filename)
        plt.gcf().savefig(filename, dpi=300)

def parse_args():
    parser = argparse.ArgumentParser(prog='graph', usage='%(prog)s [options]')
    parser.add_argument('measurements', nargs="+", help="benchmark data")
    return parser.parse_args()

if __name__ == "__main__":
    main()
