import os
import sys
import pandas as pd
import metadata

def load_timeseries(filename, service):
    df = pd.read_csv(filename, sep="\t", index_col='time', parse_dates=True)
    if "cpu" in df and not df["cpu"].isnull().all():
        df = df[df["cpu"].isnull() | (df["cpu"] == "cpu-total")]
    return df[service["fields"]]

def filter_constant_series(df):
    columns = []
    for c in df.columns:
        if df[c].isnull().any() or df[c].var() == 0:
            continue
        columns.append(c)
    return df[columns]

def interpolate_missing(df):
    # might improve accuracy
    # df = df.interpolate(method="time", limit_direction="both")
    # df.fillna(method="bfill", inplace=True)
    df = df.resample("500ms").mean()
    df.interpolate(method="time", limit_direction="both", inplace=True)
    df.fillna(method="bfill", inplace=True)
    return df

def apply(path):
    data = metadata.load(path)
    for service in data["services"]:
        filename = os.path.join(path, service["filename"])
        df = load_timeseries(filename, service)
        df2 = filter_constant_series(interpolate_missing(df))
        newname = service["name"] + "-preprocessed.tsv"
        df2.to_csv(os.path.join(path, newname), sep="\t")
        service["preprocessed_filename"] = newname
        service["preprocessed_fields"] = [c for c in df2.columns]
    metadata.save(path, data)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write("USAGE: %s measurements\n" % sys.argv[0])
        sys.exit(1)

    for p in sys.argv[1:]:
        apply(p)
