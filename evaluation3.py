from plot import plt, sns
import pandas as pd
import argparse
import numpy as np
import sys
import os
from collections import defaultdict

def main():
    df = pd.read_csv(sys.argv[1])
    plot = sns.barplot(x="type", y="time", data=df, palette="Set3")
    plt.savefig("time-overhead-sysdig.png")

if __name__ == "__main__":
    main()
