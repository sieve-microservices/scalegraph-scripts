from plot import plt, sns, rescale_barplot_width
import matplotlib as mpl
import pandas as pd
import argparse
import numpy as np
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser(prog='graph', usage='%(prog)s [options]')
    parser.add_argument('tsv', help="benchmark data")
    return parser.parse_args()

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

# TODO get blkio
# columns = ['blkio_read', 'blkio_write', 'cpu_usage', 'db_size','netio_read', 'netio_write']
columns = ['cpu_usage', 'db_size','netio_read', 'netio_write']
translate = {
        'cpu_usage' : "CPU time",
        'db_size': "DB size",
        'netio_read': "Incoming\ntraffic",
        'netio_write': "Outgoing\ntraffic",
}

X = "Metric"
Y = "Value for reduced metrics / Value of all metrics"

def main():
    args = parse_args()
    df = pd.read_csv(args.tsv, sep="\t")
    data = defaultdict(list)
    for c in columns:
        for row in np.nditer(df[c + "_reduced"] / df[c + "_native"]):
            data[X].append(translate[c])
            data[Y].append(row.min())
    plt.clf()
    #sns.set_palette(sns.color_palette(palette="gray", n_colors=4, desat=0.4))
    plot = sns.barplot(x=X, y=Y, data=pd.DataFrame(data))
    rescale_barplot_width(plot, color="k")
    plt.ylabel(r"$\frac{\text{Value of reduced metric}}{\text{All metrics}}$", fontsize=24)
    plt.tight_layout()
    plt.savefig("measurement-reduction.pdf", dpi=300)

if __name__ == "__main__":
    main()
