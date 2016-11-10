from plot import plt, sns
import pandas as pd
import argparse
import numpy as np
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser(prog='graph', usage='%(prog)s [options]')
    parser.add_argument('tsv', help="benchmark data")
    return parser.parse_args()

# TODO get blkio
# columns = ['blkio_read', 'blkio_write', 'cpu_usage', 'db_size','netio_read', 'netio_write']
columns = ['cpu_usage', 'db_size','netio_read', 'netio_write']

X = "Metric"
Y = "Value"

def main():
    args = parse_args()
    df = pd.read_csv(args.tsv, sep="\t")
    data = defaultdict(list)
    for c in columns:
        for row in np.nditer(df[c + "_reduced"] / df[c + "_native"]):
            data[X].append(c)
            data[Y].append(row.min())
    plot = sns.barplot(x=X, y=Y, data=pd.DataFrame(data))
    plt.savefig("measurement-reduction.png")

if __name__ == "__main__":
    main()
