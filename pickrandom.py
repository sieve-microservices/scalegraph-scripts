from plot import plt, sns
import pandas as pd
import argparse
import numpy as np
from numpy.random import choice
import math
from collections import defaultdict
import metadata
import os
import re
from sklearn import metrics

from graphs import cycle, draw_sbd_bar_plot
from kshape import _sbd
import matplotlib.gridspec as gridspec

def load_cluster_assignments(measurements):
    all_measurements = defaultdict(list)
    for m in measurements:
        data = metadata.load(m)
        for srv in data["services"]:
            if srv["name"] == "loadgenerator":
                continue
            selected = max(srv["clusters"], key=lambda x: srv["clusters"][x]['silhouette_score'])

            for k, c in srv["clusters"].items():
                all_measurements["measurement"].append(m)
                all_measurements["service"].append(srv["name"])
                all_measurements["cluster_size"].append(int(k))
                all_measurements["silhouette_score"].append(c["silhouette_score"])
                all_measurements["selected"].append(k == selected)
                filenames = []
                for name in c["filenames"]:
                   filenames.append(os.path.join(m, name))
                all_measurements["filenames"].append(filenames)
    return pd.DataFrame(all_measurements)

def draw_series_seperate(df, ax):
    df2 = df.copy()
    for i, c in enumerate(df2.columns):
        df2[c] += 8 * i
    ax.set_title("Comparision of zscore(t)")
    ax.set_prop_cycle(cycle())
    df2.plot(ax=ax)
    ax.legend().remove()
    ax.yaxis.set_visible(False)
    ax.set_ylabel("zscore(t)")
    ax.set_ylim([-2, 8 * (len(df2.columns) + 1)])

def print_cluster(idx, cluster):
    imgs = ""
    size = cluster.cluster_size
    for i, name in enumerate(cluster.filenames):
        df = pd.read_csv(name, sep="\t", index_col='time', parse_dates=True)

        columns = list(df.columns)
        columns.remove("centroid")
        columns = ["centroid"] + columns
        df.reindex_axis(columns, axis=1)

        new_names = {}
        for c in columns:
            new_names[c] = re.sub(r'^[^-]+-(.*)', r'\1', c)
        df.rename(columns=new_names, inplace=True)

        if len(df.columns) <= 1:
            size -= 1
            continue
        if len(df.columns) > 15 and False:
           fig = plt.figure(figsize=(15, 5))
           gs = gridspec.GridSpec(3, 2)
           ax1 = plt.subplot(gs[0, :2])
           ax2 = plt.subplot(gs[0, 1])
           ax3 = plt.subplot(gs[2, 0])
        else:
           fig = plt.figure(figsize=(10, 5))
           gs = gridspec.GridSpec(2, 2)
           ax1 = plt.subplot(gs[:, 0])
           ax2 = plt.subplot(gs[0, 1])
           ax3 = plt.subplot(gs[1, 1])

        draw_series_seperate(df, ax1)
        ax2.axis('off')
        ax2.legend(*ax1.get_legend_handles_labels(), loc='upper left', ncol=2)

        if df.centroid.notnull().any() and df.centroid.var() != 0:
            distances = []
            for c in df.columns:
                if c == "centroid": continue
                distances.append(_sbd(df.centroid, df[c])[0])
            draw_sbd_bar_plot(distances, ax3)
            ax3.yaxis.tick_right()

        image = os.path.basename(name.replace(".tsv.gz", ".pdf"))
        plt.savefig(image, dpi=200)
        plt.close("all")
        imgs += '<img src="%s" alt="%s"></img>\n' % (image, image)

    print("<p><h2>No %d, Service: %s, Size: %d, Silhouette Score: %f<h2/>\n%s</p>" %
            (idx, cluster.service, size, cluster.silhouette_score, imgs))

def main():
    args = parse_args()
    df = load_cluster_assignments(args.measurements)
    df = df[(df.measurement == df.measurement.unique()[0]) & (df.selected)]
    df = df.sort_values("silhouette_score")

    bottom = df.iloc[0]
    middle = df[df.service == "real-time"].iloc[0]
    #middle = df[math.floor(len(df) / 3):math.floor(2 / 3.0 * len(df))].sample(1)
    top = df.iloc[-1]

    print("<html><head></head><body>")

    print("<h1>Upper-quality cluster</h1>")
    print_cluster(1, top)

    print("<h1>Middle-quality cluster</h1>")
    print_cluster(2, middle)

    print("<h1>Lower-quality cluster</h1>")
    print_cluster(3, bottom)

    print("</body></html>" )

def parse_args():
    parser = argparse.ArgumentParser(prog='graph', usage='%(prog)s [options]')
    parser.add_argument('measurements', nargs="+", help="benchmark data")
    return parser.parse_args()

if __name__ == "__main__":
    main()
