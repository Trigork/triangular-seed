#!/usr/bin/env python

import json
import urllib2
import time
import sys
from time import sleep

def extract_stats(statline):
    s = statline.split(',')
    return (s[0],s[3],s[4],s[5])

# Server providing usage DB, use localhost if this will run on the router itself
server = 'http://router.lan/usage/'
usage_file = 'usage.db'

# Absolute route to the stats DB file
usage_db = '/var/www/html/netstats/stats.json'
tmax_stored = 2592000000

# Check if stats DB file exists, if not, create it with "[]"
try:
    f = open(usage_db, 'r')
except IOError:
    f = open(usage_db, 'w')
    f.write("[]")

while True:
    try:
        response = urllib2.urlopen(server+usage_file)
    except urllib2.HTTPError as e:
        continue
    except urllib2.URLError as e:
        continue

    timems = int(round(time.time() * 1000))

    statlines = response.readlines()
    statlines.pop(0)
    stats = map(extract_stats, statlines)

    with open(usage_db, 'r') as f:
        json_data = json.load(f)
        stats_dict = {"time": timems, "stats": [], "global": {}}
        for s in stats:
            stats_dict['stats'].append({"mac": s[0], "down": 0, "up": 0, "totaldown": int(s[1]), "totalup": int(s[2]), "total": int(s[3])})
        if len(json_data) > 0:
            if (timems - json_data[0]["time"]) >= tmax_stored:
                json_data.pop(0)
            prev_data = json_data[-1]
            for idx,act in enumerate(stats_dict["stats"]):
                prev_list = list(filter(lambda d: d["mac"] == act["mac"], prev_data["stats"]))
                if len(prev_list) > 0:
                    prev = prev_list[0]
                    tdif = stats_dict["time"] - prev_data["time"]
                    tdif_secs = int(tdif/1000)
                    stats_dict["stats"][idx]["down"] = (act["totaldown"] - prev["totaldown"])/tdif_secs
                    stats_dict["stats"][idx]["up"] = (act["totalup"] - prev["totalup"])/tdif_secs
        stats_dict["global"] = reduce((lambda d1, d2: {"down": d1["down"] + d2["down"], "up": d1["up"] + d2["up"], "totaldown": d1["totaldown"] + d2["totaldown"], "totalup": d1["totalup"] + d2["totalup"], "total": d1["total"] + d2["total"]}), stats_dict['stats'])
        json_data.append(stats_dict)

    with open(usage_db, 'w') as f:
        f.write(json.dumps(json_data))

    sleep(5)
