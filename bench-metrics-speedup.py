from influxdb import InfluxDBClient
from pandas.tseries.offsets import DateOffset
import pandas as pd
import subprocess
import time
import argparse
import metadata
import os
import json
from plot import plt, sns
from docker import Client
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser(prog='bench-metrics-speedup', usage='%(prog)s [options]')
    parser.add_argument('measurements', nargs="+", help="measurement directories")
    return parser.parse_args()

class Container():
    def __init__(self, **kwargs):
        self.api = Client()
        self.container_args = kwargs

    def stats(self):
        s = next(self.api.stats(self.id))
        return json.loads(s.decode("utf-8"))

    def inspect(self):
        return self.api.inspect_container(self.id)

    def inspect_volume(self, id):
        return self.api.inspect_volume(id)

    def __enter__(self):
        self.id = self.api.create_container(**self.container_args).get("Id")
        self.api.start(container=self.id)
        data = self.api.inspect_container(self.id)
        self.ip = data["NetworkSettings"]["IPAddress"]
        return self

    def __exit__(self, type, value, tb):
        self.api.stop(container=self.id)
        self.api.remove_container(container=self.id)

def insert_influxdb(client, path, reduced_set=False):
    m = metadata.load(path)
    for srv in m["services"]:
        if srv["name"] in ["loadgenerator"]:
            continue
        if srv["name"] != "web":
            continue
        print(srv["name"])
        if reduced_set:
            for k, cluster in srv["clusters"].items():
                granger_fields = cluster.get("grangercausality-metrics")
                if granger_fields is not None:
                    break
            assert granger_fields is not None, "No grangercausality-metrics found"
            fields = []
            for f in granger_fields:
                if f is None:
                    continue
                fields.append(f.replace("-diff", ""))
        else:
            fields = srv["fields"]

        df = pd.read_csv(os.path.join(path, srv["filename"]), sep="\t", parse_dates=True, index_col='time')
        points = []
        filtered_fields = fields + srv["tags"]
        df = df[filtered_fields]
        start = df.iloc[0].name
        end = start + DateOffset(minutes=10)

        df = df[(df.index >= start) & (df.index <= end)]

        for idx, series in df.iterrows():
            f = dict(series[fields][series.notnull()])
            if len(f) == 0:
                continue
            point = {
                "time": idx,
                "measurement": srv["name"],
                "fields": dict(f),
                "tags": dict(series[srv["tags"]][series.notnull()]),
            }
            points.append(point)
            if len(points) > 1000:
                client.write_points(points)
                points.clear()
        if len(points) > 0:
            client.write_points(points)

def get_io(obj):
    read = 0
    write = 0
    for item in obj["blkio_stats"]["io_service_time_recursive"]:
        if item["op"] == "Read":
            read += item["value"]
        if item["op"] == "Write":
            write += item["value"]
    return read, write

def du(path):
    out = subprocess.check_output(["sudo", "du", "-s", path])
    return int(out.decode("utf-8").split("\t")[0])

def packet_size(data, key):
    return int(data["networks"]["eth0"][key])

def benchmark_import(stats, path, reduced_set=False):
    with Container(image='influxdb:alpine', ports=[8083, 8086]) as container:
        time.sleep(2)
        client = InfluxDBClient(container.ip, 8086, database="metrics")
        client.create_database("metrics")
        time.sleep(2)
        before = container.stats()
        mountpoint = os.path.join(container.inspect()["Mounts"][0]["Source"])
        before_size = du(mountpoint)

        result = client.query('show stats;')
        insert_influxdb(client, path, reduced_set)
        after = container.stats()
        container.api.stop(container=container.id)
        after_size = du(mountpoint)
        stats["cpu_usage"].append(after["cpu_stats"]["cpu_usage"]["total_usage"] - before["cpu_stats"]["cpu_usage"]["total_usage"])
        import pdb; pdb.set_trace()
        stats["blkio_read"].append(get_io(after)[0] - get_io(before)[0])
        stats["blkio_write"].append(get_io(after)[1] - get_io(before)[1])
        stats["netio_read"].append(packet_size(after, "rx_packets") - packet_size(before, "rx_packets"))
        stats["netio_write"].append(packet_size(after, "tx_packets") - packet_size(before, "tx_packets"))
        stats["db_size"].append(after_size - before_size)

def main():
    args = parse_args()
    stats1 = defaultdict(list)
    stats2 = defaultdict(list)
    for m in args.measurements:
        stats1["measurement"].append(m)
        benchmark_import(stats1, m)
        stats2["measurement"].append(m)
        benchmark_import(stats2, m, reduced_set=True)
    df = pd.DataFrame(stats1).merge(pd.DataFrame(stats2), on='measurement', suffixes=["_native", "_reduced"])
    df.to_csv("result2.tsv", sep="\t")

if __name__ == '__main__':
    main()
