from plot import plt, sns, mpl
import pandas as pd
import argparse
import numpy as np
import sys
import os
from collections import defaultdict

def graph1(df):
    X = "Service"
    Y = "Reduction [%]"
    df[Y] = ((df["#Metrics"] - df["Best"]) / df["#Metrics"])
    df = df.rename(columns={'Name': X})
    plot = sns.barplot(x=X, y=Y, data=df, color="k")
    plot.set_xticklabels(plot.get_xticklabels(), rotation='vertical')
    plt.savefig("metric-reduction-1.pdf")

SERVICE_TABLE = {
  "track-changes": "track-ch.",
  "doc-updater":  "doc-upd.",
}

FONT_SIZE=30
plt.rcParams.update({
    "font.size": FONT_SIZE,
    "axes.labelsize" : FONT_SIZE,
    "font.size" : FONT_SIZE,
    "text.fontsize" : FONT_SIZE,
    "legend.fontsize": FONT_SIZE * 0.7,
    "xtick.labelsize" : FONT_SIZE * 0.8,
    "ytick.labelsize" : FONT_SIZE * 0.8,
    })

def graph2(df):
    X = "Service"
    Y = "Number of metrics"
    HUE = "when"
    data = defaultdict(list)
    for _, row in df[["Name", "#Metrics", "Best"]].iterrows():
        if row["Name"] in ["loadgenerator", "track-changes", "web"]:
            continue
        data[X].append(SERVICE_TABLE.get(row["Name"], row["Name"]))
        data[Y].append(row["#Metrics"])
        data[HUE].append("Before clustering")
        data[X].append(SERVICE_TABLE.get(row["Name"], row["Name"]))
        data[Y].append(row["Best"])
        data[HUE].append("After clustering")
    plot = sns.barplot(x=X, y=Y, hue=HUE, data=pd.DataFrame(data), palette="gray")
    plot.set_yscale("log")
    plt.legend(title='',
               bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=2, mode="expand", borderaxespad=0.)
    plot.set(ylabel="Number of metrics", xlabel="")
    plot.set_xticklabels(plot.get_xticklabels(), rotation=65, ha="right")
    plt.tight_layout()
    plt.savefig("metric-reduction-2.pdf", dpi=300)

def main():
    df = pd.read_html(sys.argv[1])[0]
    df = df[["Name", "#Metrics", "Best"]]
    graph1(df)
    graph2(df)


if __name__ == "__main__":
    main()
