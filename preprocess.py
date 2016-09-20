import os
import sys
import argparse

import pandas as pd
import numpy as np

import metadata
from kshape import zscore

def load_timeseries(filename, service):
    df = pd.read_csv(filename, sep="\t", index_col='time', parse_dates=True)
    if "cpu" in df and not df["cpu"].isnull().all():
        df = df[df["cpu"].isnull() | (df["cpu"] == "cpu-total")]
    return df[service["fields"]]

def is_monotonic(serie):
    if serie.dtype == np.float64:
        return pd.algos.is_monotonic_float64(serie.values, False)[0]
    elif serie.dtype == np.int64:
        return pd.algos.is_monotonic_int64(serie.values, False)[0]
    else:
        raise ValueError("unexpected column type: %s" % serie.dtype)

def classify_series(df):
    classes = {
      "empty_fields": [],
      "constant_fields": [],
      "low_frequency": [],
      "low_variance_fields": [],
      "monotonic_fields": [],
      "other_fields": [],
    }
    for c in df.columns:
        column = df[c].dropna()
        if len(column) == 0:
            key = "empty_fields"
        elif len(column)/len(df[c]) <= 0.002:
            key = "low_frequency"
        elif column.var() == 0:
            key = "constant_fields"
        elif zscore(column).var() <= 1e-2:
            key = "low_variance_fields"
        elif is_monotonic(column):
            key = "monotonic_fields"
        else:
            key = "other_fields"
        classes[key].append(c)
    return classes

def interpolate_missing(df, sampling_rate):
    df = df.resample("500ms").mean()
    cols = {}
    for col in df.columns:
        cols[col] = df[col].interpolate(method="spline", limit=2 * int(1/sampling_rate), order=3)
    df2 = pd.DataFrame(cols)
    return df2.fillna(value=0)

def diff(df, monotonic_fields):
    montonic = set(monotonic_fields)
    series = {}
    for c in df.columns:
        if c in montonic:
            series[c + "-diff"] = df[c].diff()[1:]
        else:
            series[c] = df[c][1:]
    return pd.DataFrame(series)

def apply(path, sampling_rate):
    data = metadata.load(path)
    for service in data["services"]:
        filename = os.path.join(path, service["filename"])
        newname = service["name"] + "-preprocessed.tsv.gz"
        service["preprocessed_filename"] = newname
        newpath = os.path.join(path, newname)
        if os.path.exists(newpath) and "other_fields" in service:
            print("skip %s" % newpath)
            #continue
        df = load_timeseries(filename, service)
        classes = classify_series(df)
        preprocessed_series = {}
        df2 = interpolate_missing(df[classes["other_fields"] + classes["monotonic_fields"]], sampling_rate)
        df3 = diff(df2, classes["monotonic_fields"])
        df3.to_csv(newpath, sep="\t", compression='gzip')
        service["preprocessed_fields"] = list(df3.columns)
        service.update(classes)
    metadata.save(path, data)

def parse_args():
    parser = argparse.ArgumentParser(usage='%(prog)s [options]')
    parser.add_argument('measurements', nargs='+', help="measurement directories to process")
    parser.add_argument('--sampling-rate', action='store_true', default=(1/2), help="how often data is updated per second")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    for p in args.measurements:
        apply(p, args.sampling_rate)
