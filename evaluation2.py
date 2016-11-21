from plot import plt, sns
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
    plot = sns.barplot(x=X, y=Y, data=df, palette="Set3")
    plot.set_xticklabels(plot.get_xticklabels(), rotation='vertical')
    plt.savefig("metric-reduction-1.pdf")

def graph2(df):
    X = "Service"
    Y = "Number of Metrics"
    HUE = "when"
    data = defaultdict(list)
    for _, row in df[["Name", "#Metrics", "Best"]].iterrows():
        data[X].append(row["Name"])
        data[Y].append(row["#Metrics"])
        data[HUE].append("#Metrics before Clustering")
        data[X].append(row["Name"])
        data[Y].append(row["Best"])
        data[HUE].append("#Metrics after Clustering")
    plot = sns.barplot(x=X, y=Y, hue=HUE, data=pd.DataFrame(data), palette="Set3")
    plot.set_xticklabels(plot.get_xticklabels(), rotation=65)
    plt.subplots_adjust(bottom=0.25)
    plt.savefig("metric-reduction-2.pdf")

def main():
    df = pd.read_html(sys.argv[1])[0]
    df = df[["Name", "#Metrics", "Best"]]
    graph1(df)
    graph2(df)


if __name__ == "__main__":
    main()
