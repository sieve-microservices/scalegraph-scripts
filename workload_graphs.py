import sys
import re
import os
import gzip
import warnings
from datetime import datetime

import pytz
import pandas as pd
from matplotlib import gridspec
import numpy as np
from collections import defaultdict

from plot import plt, sns

METHODS = [
    "GET",
    "HEAD",
    "POST",
    "PUT",
    "DELETE",
    "TRACE",
    "OPTIONS",
    "CONNECT",
    "OTHER_METHODS",
]

TYPES = [
    "HTML",
    "IMAGE",
    "AUDIO",
    "VIDEO",
    "JAVA",
    "FORMATTED",
    "DYNAMIC",
    "TEXT",
    "COMPRESSED",
    "PROGRAMS",
    "DIRECTORY",
    "ICL",
    "OTHER_TYPES",
    "NUM_OF_FILETYPES",
]

STATUS = [
    "100",
    "101",
    "200",
    "201",
    "202",
    "203",
    "204",
    "205",
    "206",
    "300",
    "301",
    "302",
    "303",
    "304",
    "305",
    "400",
    "401",
    "402",
    "403",
    "404",
    "405",
    "406",
    "407",
    "408",
    "409",
    "410",
    "411",
    "412",
    "413",
    "414",
    "415",
    "500",
    "501",
    "502",
    "503",
    "504",
    "505",
    "OTHER_CODES",
]

REGIONS = ["SantaClara", "Plano", "Herndon", "Paris"]

def request_type():
    """
struct request {
 uint32_t timestamp;
 uint32_t clientID;
 uint32_t objectID;
 uint32_t size;
 uint8_t method;
 uint8_t status;
 uint8_t type;
 uint8_t server;
};
    """
    def i(name): return (name, '>u4')
    def b(name): return (name, 'b')
    return np.dtype([i('timestamp'),
                     i('client_id'),
                     i('object_id'),
                     i('size'),
                     b('method'),
                     b('status'),
                     b('type'),
                     b('server')])

def inverse_dict(map):
    return dict((v, k) for k, v in map.iteritems())

def read_worldcup_log(path):
    buf = gzip.open(path, "r").read()
    df = pd.DataFrame(np.frombuffer(buf, dtype=request_type()))
    timestamp = df.timestamp.values.astype(np.int64)

    from_codes = pd.Categorical.from_codes
    fields = dict(timestamp=timestamp.view("datetime64[s]"),
                  client_id=df.client_id,
                  object_id=df.object_id,
                  size=df.size,
                  method=from_codes(df.method, categories=METHODS),
                  status=from_codes(df.status & 0x3f, categories=STATUS),
                  type=from_codes(df.type, categories=TYPES),
                  region=from_codes(df.server.apply(lambda x: x >> 5), categories=REGIONS),
                  server=df.server & 0x1F)
    return pd.DataFrame(fields)

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

def parse_datetime(x):
    """
    Parses datetime with timezone formatted as: `[day/month/year:hour:minute:second zone]`
    Example:
         `>>> parse_datetime('13/Nov/2015:11:45:42 +0000')`
         `datetime.datetime(2015, 11, 3, 11, 45, 4, tzinfo=<UTC>)`

    Due to problems parsing the timezone (`%z`) with `datetime.strptime`, the
    timezone will be obtained using the `pytz` library.
    """
    if x == "-" or x == "" or x is None: return None
    dt = datetime.strptime(x[1:-7], '%d/%b/%Y:%H:%M:%S')
    dt_tz = int(x[-6:-3]) * 60 + int(x[-3:-1])
    return dt.replace(tzinfo=pytz.FixedOffset(dt_tz))

def read_common_log(path):
    # example line:
    # 199.72.81.55 - - [01/Jul/1995:00:00:01 -0400] "GET /history/apollo/ HTTP/1.0" 200 6245
    parts = [
              r'(?P<host>\S+)',                   # host %h
              r'\S+',                             # indent %l (unused)
              r'(?P<user>\S+)',                   # user %u
              r'(?P<time>.+)',                    # time %t
              r'"(?P<method>\S+)\s+(?P<ressource>[^" ]+)([^"]+)?"', # request "%r"
              r'(?P<status>[0-9]+)',              # status %>s
              r'(?P<size>\S+)',                   # size %b (careful, can be '-')
    ]
    regex = r'\s+'.join(parts)+r'\s*\Z'
    pattern = re.compile(regex)

    log = defaultdict(list)
    with gzip.open(path, "r") as f:
        for line in f:
            line = line.decode("latin_1")
            m = pattern.match(line)
            if m is None:
                warnings.warn("ignore invalid log line '%s'" % line)
                continue
            res = m.groupdict()
            log["client_id"].append(res["host"])
            log["timestamp"].append(parse_datetime(res["time"]))
            log["method"].append(res["method"])
            log["ressource"].append(res["ressource"])
            log["status"].append(res["status"])
            if res["size"] != "-":
                size = int(res["size"])
            else:
                size = None
            log["size"].append(size)
            ressource = res["ressource"].lower()
            filename, ext = os.path.splitext(ressource)
            ext = ext.lower()
            if ext.endswith("."):
                ext = ext[:-1]

            if ressource.endswith("/") or ext == "" or ext in [".gov"]:
                type = "DIRECTORY"
            elif ".htm" in ressource or ext in [".txt", ".txt~", ".hmtl", ".htlm", ".hrml", ".bak"]:
                type = "HTML"
            elif ext in [".gif", ".xbm", ".jpg", ".jpeg", ".bmp"]:
                type = "IMAGE"
            elif ext in [".wav"]:
                type = "AUDIO"
            elif ext in [".mpg"]:
                type = "VIDEO"
            elif "cgi" in ressource or "?" in ressource or ext in [".pl", ".perl"]:
                type = "DYNAMIC"
            #elif ext in [".pdf", ".zip"]:
            else:
                type = "OTHER_TYPES"
            log["type"].append(type)
    log["status"] = pd.Categorical(log["status"], categories=STATUS, ordered=False)
    log["method"] = pd.Categorical(log["method"], categories=METHODS, ordered=False)
    return pd.DataFrame(log)


def main(type, args):
    logs = []
    if type == "worldcup":
        read_log = read_worldcup_log
    elif type == "nasa":
        read_log = read_common_log
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
    #request_rate(df, title[type], "requests-per-time-%s.png" % type)
    #retention_time(df, "rentention-time-%s.png" % type)
    #user_requests(df, "user-requests-%s.png" % type)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("Draw graphs for nasa95 and worldcup97 web logs\n")
        sys.stderr.write("USAGE: %s type logfile\n")
        sys.exit(1)
    type = sys.argv[1]
    args = sys.argv[2:]
    main(type, args)
