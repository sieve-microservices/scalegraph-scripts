from plot import plt, sns, rescale_barplot_width
import matplotlib as mpl
from matplotlib.ticker import FormatStrFormatter
import pandas as pd
import argparse
import numpy as np
from collections import defaultdict
import statsmodels.stats.api as sms

def parse_args():
    parser = argparse.ArgumentParser(prog='graph', usage='%(prog)s [options]')
    parser.add_argument('tsv', help="benchmark data")
    return parser.parse_args()

FONT_SIZE=30
plt.rcParams.update({
    "font.size": FONT_SIZE,
    "axes.labelsize" : FONT_SIZE,
    "font.size" : FONT_SIZE,
    "text.fontsize" : FONT_SIZE,
    "legend.fontsize": FONT_SIZE,
    "xtick.labelsize" : FONT_SIZE * 0.9,
    "ytick.labelsize" : FONT_SIZE,
    })

# TODO get blkio
# columns = ['blkio_read', 'blkio_write', 'cpu_usage', 'db_size','netio_read', 'netio_write']
columns = ['cpu_usage', 'db_size','netio_read', 'netio_write']
translate = {
        'cpu_usage' : "CPU time [s]",
        'db_size': "DB size [KB]",
        'netio_read': "Traffic In [MB]",
        'netio_write': "Traffic Out [KB]",
}

X = "Metric"
Y = "Reduction [%]"
A = "Before"
B = "After"

def main():
    args = parse_args()
    df = pd.read_csv(args.tsv, sep="\t")
    data = defaultdict(list)
    c = ["netio_write_reduced", "netio_write_native"]
    df[c] = df[c].apply(lambda x: x / 1e3) # KB
    c = ["netio_read_reduced", "netio_read_native"]
    df[c] = df[c].apply(lambda x: x / 1e6) # MB

    for c in columns:
        for i, row in enumerate(np.nditer(100 - df[c + "_reduced"] / df[c + "_native"] * 100)):
            data[X].append(translate[c])
            data[A].append(df[c + "_native"][i])
            data[B].append(df[c + "_reduced"][i])
            data[Y].append(row.min())
    df2 = pd.DataFrame(data)
    df3 = df2.groupby("Metric").agg({A: "mean", B: "mean", Y: "mean"})
    df3 = df3[[A, B, Y]]
    print(df3.to_latex().replace("±", "$\pm$"))
    #plt.clf()
    #sns.set_palette(sns.color_palette(palette="gray", n_colors=4, desat=0.4))
    #plot = sns.barplot(x=X, y=Y, data=pd.DataFrame(data))
    #rescale_barplot_width(plot)
    #plt.ylabel(r"$\frac{\text{Value of reduced metric}}{\text{All metrics}}$", fontsize=FONT_SIZE)
    #plot.yaxis.set_units('%')
    #plt.tight_layout()
    #plt.savefig("measurement-reduction.pdf", dpi=300)

if __name__ == "__main__":
    main()
