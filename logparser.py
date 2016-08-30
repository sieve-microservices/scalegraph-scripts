import sys
import re
import os
import gzip
import warnings
from datetime import datetime

import pytz
import pandas as pd
import numpy as np
from collections import defaultdict

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

def read_worldcup(path):
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

def read_nasa(path):
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
            else:
                type = "OTHER_TYPES"
            log["type"].append(type)
    log["status"] = pd.Categorical(log["status"], categories=STATUS, ordered=False)
    log["method"] = pd.Categorical(log["method"], categories=METHODS, ordered=False)
    return pd.DataFrame(log)
