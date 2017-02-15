from plot import plt, sns, rescale_barplot_width
import pandas as pd
import argparse
import numpy as np
import sys
import os
from collections import defaultdict

TIME="Time to complete 10,000 requests"
TYPE="Type"

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

def main():
    df = pd.read_csv(sys.argv[1])
    df.rename(columns={"time": TIME, "type": TYPE}, inplace=True)
    sns.set_palette(sns.color_palette(palette="gray", n_colors=3, desat=0.4))
    plot = sns.barplot(x=TYPE, y=TIME, data=df)
    rescale_barplot_width(plot, 0.6)

    plt.ylabel(TIME)
    plt.tight_layout()
    plt.savefig("time-overhead-sysdig.pdf")

if __name__ == "__main__":
    main()
