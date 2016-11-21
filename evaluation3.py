from plot import plt, sns
import pandas as pd
import argparse
import numpy as np
import sys
import os
from collections import defaultdict

TIME="time to complete 10,000 requests"

def main():
    df = pd.read_csv(sys.argv[1])
    df.rename(columns={"time": TIME}, inplace=True)
    plot = sns.barplot(x="type", y=TIME, data=df, palette="Set3")
    plt.savefig("time-overhead-sysdig.pdf")

if __name__ == "__main__":
    main()
