import re
import argparse

import pandas as pd
from scipy.stats import zscore
import numpy as np

from plot import plt, sns
from matplotlib.ticker import MultipleLocator

def parse_args():
    parser = argparse.ArgumentParser(prog='linearmodel_graphs', usage='%(prog)s [options]')
    parser.add_argument('linearmodel', help="linear relations")
    return parser.parse_args()

def get_diff(df):
    df_a = df[df.scale == 1]
    df_b = df[df.scale != 1]

    merge = df_a.merge(df_b, on=["service-a", "service-b", "metric-a", "metric-b"], how='inner', suffixes=('-x', '-y'))
    merge["slope-diff"] = pd.Series(merge["slope-y"] / merge["slope-x"], index=merge.index)
    merge["quotient-diff"] = pd.Series(merge["quotient-y"] / merge["quotient-x"], index=merge.index)
    return merge

def write_summary(target, df):
    with open(target, "w+") as f:
        for scale in df["scale-y"].unique():
            f.write("<h1>scale-y: %d</h1>\n" % scale)
            f.write(df[df["scale-y"] == scale].describe().to_html())
            f.write("\n")

def main():
    args = parse_args()
    df = pd.read_csv(args.linearmodel, sep="\t")
    df.columns = df.columns.str.replace("_", "-")
    significant = df[df["p-value"] < 0.10]
    first_of_each_scale = significant[significant["name"].isin(significant.groupby(["scale"]).nth(1).name.unique())]
    diff = get_diff(df)

    plt.axes().yaxis.set_minor_locator(MultipleLocator(1))

    plt.subplots_adjust(top=0.85)
    plot = sns.factorplot("slope-diff", col="scale-y", data=diff[(diff["slope-diff"] < 15) & (diff["slope-diff"] > -15)], kind="violin")
    plot.set(xlabel=r'$\displaystyle -15 < \frac{slope_{scale_y}}{slope_{scale_1}} < 15$')
    plot.savefig("relative_slope_increasing_scale.png", dpi=300)
    plot.fig.suptitle("Relative Slope difference of linear models with increasing scale")

    g = sns.FacetGrid(first_of_each_scale, col="scale")
    g = g.map(plt.hist, "slope", bins=np.arange(-1, 1 + 0.1, 0.1))
    g.savefig("slope-distribution.png")

    g = sns.FacetGrid(first_of_each_scale, col="scale")
    g = g.map(plt.hist, "quotient", bins=np.arange(-1, 1 + 0.1, 0.1))
    g.savefig("quotient-distribution.png")

    plt.clf()
    g = sns.countplot("name", data=first_of_each_scale.groupby(["service-a", "service-b", "metric-a", "metric-b"])["name"].count().reset_index())
    g.set(ylabel="number of common relationships across scale")
    g.get_figure().savefig("common_relations_across_scale.png")

    g = sns.FacetGrid(significant.groupby(["service-a", "service-b", "metric-a", "metric-b", "scale"]).count().reset_index(), col="scale")
    g.map(plt.hist, "name")
    g.set(ylabel="Common relations count per metric")
    g.fig.savefig("common_relations_same_scale.png")

    plt.clf()
    g = sns.countplot("name", data=first_of_each_scale[first_of_each_scale.scale != 1].groupby(["service-a", "service-b", "metric-a", "metric-b"])["name"].count().reset_index())
    g.set(ylabel="number of common relationships excluding 1")
    g.get_figure().savefig("common_relations_across_scale_without_1.png")

    #metrics = grouped.filter(lambda x: x.count() == 4)
    #describe = metrics.groupby([df.service, df.metric]).describe().unstack()

    #plt.clf()
    #g = sns.countplot("scale", data=first_of_each_scale)
    #g.set(ylabel="Number of linear relations with $p < 0.10$")
    #g.get_figure().tight_layout()
    #g.get_figure().savefig("significant-count-10percent.png")

    #plt.clf()
    #significant5 = df[(df["p-value"] < 0.5)]
    #first_of_each_scale5 = significant5.groupby(["service-a", "service-b", "metric-a", "metric-b", "scale"]).nth(1).reset_index()
    #g = sns.countplot("scale", hue="lower10", data=first_of_each_scale5)
    #g.set(ylabel="Number of linear relations with $p < 0.5$")
    #g.get_figure().tight_layout()
    #g.get_figure().savefig("significant-count-5percent.png")

    #g = sns.FacetGrid(significant.groupby(["service-a", "service-b", "metric-a", "metric-b", "scale"]), col="scale")
    #g = g.map(plt.hist, "quotient", bins=np.arange(-1, 1 + 0.1, 0.1))
    #g.savefig("quotient-distribution.png")

    write_summary("relative_slope_increasing_scale.html", diff)

    plot = sns.factorplot("quotient-diff", col="scale-y", data=diff[(diff["quotient-diff"] < 15) & (diff["quotient-diff"] > -15)], kind="violin")
    plot.set(xlabel=r'$\displaystyle -15 < \frac{quotient_{scale_y}}{quotient_{scale_1}} < 15$')
    plot.fig.suptitle("Relative Quotient difference of linear with increasing scale")
    plot.savefig("relative_quotient_increasing_scale.png", dpi=300)
    write_summary("relative_quotient_increasing_scale.html", diff)

    import pdb; pdb.set_trace()


if __name__ == "__main__":
    main()
