import sys
import pandas as pd
from matplotlib import gridspec
import numpy as np
import logparser

from plot import plt, sns

def add_text(axe, text):
    axe.axis('off')
    axe.set(xlabel="")
    axe.text(0.5, 0.3, text,
             horizontalalignment='center',
             verticalalignment='center',
             fontsize='small',
             transform = axe.transAxes)


def describe_series(series, filename):
    fig, axis = plt.subplots(3)
    ax = sns.boxplot(series, ax=axis[0])
    ax.set(ylabel='Number of users', xlabel='')
    ax = sns.distplot(series, ax=axis[1], kde=False, norm_hist=False)
    ax.set(ylabel='Number of users', xlabel='')
    add_text(axis[2], series.describe())

    fig.savefig(filename)


def retention_time(df, filename):
    g = df.groupby([pd.Grouper(key='timestamp', freq='1d'), df.client_id])
    retention_time = g.nth(-1).timestamp - g.nth(0).timestamp
    seconds = retention_time / np.timedelta64(1, 'm')
    seconds = seconds.mean(level=1)
    seconds.name = "Daily retention time [min]"
    describe_series(seconds, filename)


def user_requests(df, filename):
    actions = df.groupby([pd.Grouper(key="timestamp", freq="1d"), df.client_id]).size()
    actions = actions.mean(level=1)
    actions.name = "Daily number of requests per User"
    describe_series(actions, filename)


def count_request(df):
    return df.pivot_table("client_id", index="timestamp", aggfunc='count')


def top5_vs_rest_requests(df, filename):
    requests = df.groupby([pd.Grouper(key="timestamp", freq="1d"), df.client_id]).size()
    requests = requests.mean(level=1)
    top5 = requests.nlargest(5).index
    fig, axis = plt.subplots(2, 2, figsize=(15, 5), gridspec_kw={'width_ratios':[3, 1]})

    top5_requests = count_request(df[df.client_id.isin(top5)]).resample("1h").sum()
    top5_requests.name = "Requests per minute of top 5 users"
    plot = top5_requests.plot(ax=axis[0, 0])
    add_text(axis[0, 1], top5_requests.describe())

    rest_requests = count_request(df[~df.client_id.isin(top5)]).resample("1h").sum()
    rest_requests.name = "Requests per minute of rest"
    plot2 = rest_requests.plot(ax=axis[1, 0])
    add_text(axis[1, 1], rest_requests.describe())

    plot.set_xlim(plot2.get_xlim())

    fig.savefig(filename)


def request_rate(df, title, filename):
    fig, axis = plt.subplots(2, 2, figsize=(15, 5), gridspec_kw={'width_ratios':[3, 1]})
    fig.suptitle(title, fontsize=14)

    agg = count_request(df)
    minutely = agg.resample("60s").sum()
    minutely.name = "Requests per minute"
    minutely.plot(ax=axis[0, 0])
    add_text(axis[0, 1], minutely.describe())

    hourly = agg.resample("1h").sum()
    hourly.plot(ax=axis[1, 0])
    hourly.name = "Requests per hour"
    add_text(axis[1, 1], hourly.describe())

    fig.savefig(filename)


def main(type, args):
    logs = []
    if type == "worldcup":
        read_log = logparser.read_worldcup
    elif type == "nasa":
        read_log = logparser.read_nasa
    else:
        sys.stderr.write("type must be nasa or worldcup")

    for arg in args:
        df = read_log(arg)
        filter_ = df["type"].isin(["HTML", "DYNAMIC", "DIRECTORY"])
        if type == "worldcup":
            filter_ = filter_ & (df.region == "Paris") & (df.server == 4)
        df = df[filter_]
        df.sort_values("timestamp", inplace=True)
        logs.append(df)
    df = pd.concat(logs)
    title = {
      "worldcup": "10 days, request rate for WorldCup98, Paris, Server 4",
      "nasa": "NASA http log, Jul95"
    }
    if type == "worldcup":
        top5_vs_rest_requests(df, "top5_vs_rest_requests.png")
    request_rate(df, title[type], "requests-per-time-%s.png" % type)
    retention_time(df, "rentention-time-%s.png" % type)
    user_requests(df, "user-requests-%s.png" % type)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("Draw graphs for nasa and worldcup web logs\n")
        sys.stderr.write("USAGE: %s nasa|worldcup logfile\n")
        sys.exit(1)
    type = sys.argv[1]
    args = sys.argv[2:]
    main(type, args)
