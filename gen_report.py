import sys
import os

from jinja2 import Environment

import metadata
import pandas as pd
from collections import defaultdict

INDEX = """
# Measurement {{title}}

## Overview
| Name | #Metrics | #Metrics exclu. constant | Cluster sizes | Silhouette score| Best | Grangercausality metrics |
|------|----------|--------------------------|---------------|-----------------|------|--------------------------|
{% for _, runs in services -%}
{% for _, r in runs.iterrows() -%}
| {{r["name"]}} | {{r["fields"]|length}} | {{r["preprocessed_fields"]|length}} | {{cluster_links(r)}} | {{silhouette_score(r)}} | {{grangercausality(r)}}
{% endfor -%}
{% endfor %}
"""

CLUSTER = """
# Measurement {{title}} with a cluster size: {{cluster_size}}

{% for name, number, url, selected_metric in clusters -%}
## Cluster {{number}}
{% if selected_metric is not none: -%}
- Selected metric for grangercausality: **{{selected_metric}}**
{% endif -%}
- ![{{name}}]({{url}})

{% endfor -%}
"""

def cluster_number(service):
    if "clusters" in service:
        return max(map(int, service["clusters"].keys()))
    else:
        return 0

def cluster_links(service):
    links = []
    for i in range(1, cluster_number(service) + 1):
        links.append("[%d](%s-%s-%d)" % (i, service.title, service["name"], i))
    return " ".join(links)

def silhouette_score(row):
    res = []
    best = -1
    best_score = -1
    for key, value in sorted(row.clusters.items(), key=lambda v: int(v[0])):
        score = value.get("silhouette_score", -1)
        res.append("%s=%.2f" % (key, score))
        if best_score < score:
            best = key
            best_score = score
    if best == -1:
        res.append("| no good cluster found")
    else:
        res.append("| [%s](%s-%s-%s)" % (best, row.title, row["name"], best))
    return " ".join(res)

def grangercausality(row):
    for key, value in row.clusters.items():
        metrics = value.get("grangercausality-metrics", None)
        if metrics is None: continue
        entries = []
        for i, metric in enumerate(metrics):
            if metric is not None:
                entries.append("%s" % metric)
        return ", ".join(entries)
    return ""

def write_template(template, path, **kwargs):
    template = Environment().from_string(template)
    content = template.render(**kwargs)
    print(path)
    with open(path, "w+") as f:
        f.write(content)

def write_measurement(measurement, report):
    if measurement.endswith("/"):
        measurement = measurement[:-1]
    title = os.path.basename(measurement)
    data = metadata.load(measurement)
    metrics_count = 0
    metrics_set = set()
    filtered_count = 0
    for srv in data["services"]:
        if "preprocessed_fields" not in srv or "clusters" not in srv:
            print("warning: no preprocessed_field found for %s/%s" % (measurement, srv["name"]))
            continue
        metrics_count += len(srv["fields"])
        metrics_set.update(srv["fields"])
        filtered_count += len(srv["preprocessed_fields"])
        for cluster_size, cluster in srv["clusters"].items():
            i = int(cluster_size)
            grangercausality_metrics = cluster.get("grangercausality-metrics", [None] * int(i))
            clusters = []
            for j in range(1, i + 1):
                name = "%s-cluster-%d_%d.png" % (srv["name"], i, j)
                url = "https://gitlab.com/micro-analytics/measurements3/raw/master/%s/%s" % (title, name)
                selected_metric = grangercausality_metrics[j - 1]
                clusters.append((name, j, url, selected_metric))
            args = dict(title=title, cluster_size=i, clusters=clusters)
            path = os.path.join(report, "%s-%s-%s.md" % (title, srv["name"], cluster_size))
            write_template(CLUSTER, path, **args)
    return title, data["services"]

def write(index_title, report, measurements):
    m = defaultdict(list)
    for measurement in measurements:
        title, services = write_measurement(measurement, report)
        for srv in services:
            for k,v in srv.items():
                m[k].append(v)
            assert "title" not in srv
            m["title"].append(title)
    df = pd.DataFrame(m).groupby("name")
    df["clusters"].fillna({})
    args = dict(silhouette_score=silhouette_score, cluster_links=cluster_links, grangercausality=grangercausality, services=df, title=title)
    index = os.path.join(report, index_title + ".md")
    write_template(INDEX, index, **args)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.stderr.write("USAGE: %s title report measurements...\n" % sys.argv[0])
        sys.exit(1)
    title = sys.argv[1]
    report = sys.argv[2]
    measurements = sys.argv[3:]
    write(title, report, measurements)
