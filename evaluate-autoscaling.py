from plot import plt, sns, rescale_barplot_width
import pandas as pd
import argparse
import numpy as np
import metadata
import os
from collections import defaultdict

FONT_SIZE=20
plt.rcParams.update({
    "font.size": FONT_SIZE,
    "axes.labelsize" : FONT_SIZE,
    "font.size" : FONT_SIZE,
    "text.fontsize" : FONT_SIZE,
    "legend.fontsize": FONT_SIZE,
    "xtick.labelsize" : FONT_SIZE,
    "ytick.labelsize" : FONT_SIZE,
    })

def parse_args():
    parser = argparse.ArgumentParser(prog='graph', usage='%(prog)s [options]')
    parser.add_argument("cpu_scaling", help="benchmark data")
    parser.add_argument("http_scaling", help="benchmark data")
    return parser.parse_args()

def load_metrics(measurement):
    data = metadata.load(measurement)
    stats = defaultdict(list)
    for srv in data["services"]:
        df = pd.read_csv(os.path.join(measurement, srv["filename"]),
                sep="\t", index_col='time', parse_dates=True)
        if srv["name"] == "loadgenerator":
            name = "loadgenerator-requests_success_90_percentile"
            percentile = df[df[name].notnull()][name]
            index = percentile.index - percentile.index[0]
            stats["time"].extend(index)
            stats["requeusts_success_90%ile"].extend(percentile)
            stats["usage_percent"].extend([np.nan] * len(percentile))
            stats["service"].extend([srv["name"]] * len(percentile))
        else:
            assert "usage_percent" in df.columns
            usage_percent = df[df.usage_percent.notnull()].usage_percent
            index = usage_percent.index - usage_percent.index[0]
            stats["time"].extend(index)
            stats["usage_percent"].extend(usage_percent)
            stats["requeusts_success_90%ile"].extend([np.nan] * len(usage_percent))
            stats["service"].extend([srv["name"]] * len(usage_percent))
    where = os.path.join(measurement, data["autoscaling"]["filename"])
    df_scaling = pd.read_csv(where, sep="\t", index_col='time', parse_dates=True)
    df_scaling.index = df_scaling.index - df_scaling.index[0]
    df_cpu = pd.DataFrame(stats, index=stats["time"])
    return df_cpu.join(df_scaling, how="outer", lsuffix='', rsuffix='_scaling')

# Comparison of CPU utilisation of web service
# Comparison of SLA-violations
# Comparison of number of needed Scaling actions

def scaling(df):
    t = df[(df.service == "web") & df.scale.notnull()]
    return t[t.scale.diff() != 0]

def sla_violations(df):
    t = df[df["requeusts_success_90%ile"] > 1500]
    return t["requeusts_success_90%ile"].count()

USUAGE="CPU Usage"
SLA="SLA violations\\(out of 1400 samples)"
SCALING_ACTIONS="Number of\\ scaling actions"
A="Default metric"
B="Sieve metric"
C="Difference [%]"

def format_float(v):
    if v == int(v):
        return str(int(v))
    else:
        return "%.2f" % v

def main():
    args = parse_args()
    df_http = load_metrics(args.http_scaling)
    df_cpu  = load_metrics(args.cpu_scaling)

    scaling_cpu = scaling(df_cpu)
    scaling_http = scaling(df_http)

    usage_cpu = df_cpu[(df_cpu.service == "web") & df_cpu.usage_percent.notnull()]
    usage_http = df_http[(df_http.service == "web") & df_http.usage_percent.notnull()]
    requests_cpu = df_http[df_http["requeusts_success_90%ile"].notnull()]
    requests_http = df_cpu[df_cpu["requeusts_success_90%ile"].notnull()]

    graph = defaultdict(list) # type: defaultdict[str, List]
    def append_metric(name, before, after):
        graph["metric"].append(name)
        graph[A].append(before)
        graph[B].append(after)
        graph[C].append((after - before)/before * 100)
    append_metric(USUAGE, usage_cpu.usage_percent.mean(), usage_http.usage_percent.mean())
    append_metric(SLA, sla_violations(requests_cpu), sla_violations(requests_http))
    append_metric(SCALING_ACTIONS, scaling_cpu.scale.count(), scaling_http.scale.count())
    df = pd.DataFrame(graph)
    df = df[["metric", A, B, C]].set_index("metric")
    table = df.to_latex(float_format=format_float, formatters={C: lambda v: ("+" if v > 0 else "") + format_float(v)})
    print(table)

if __name__ == "__main__":
    main()
