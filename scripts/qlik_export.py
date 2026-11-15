"""Export the raw EPA weekly cyanoHAB forecast table from the public Qlik app via
Engine API GetTableData (raw table rows, no aggregation). Read-only."""
import csv, json, ssl, sys, hashlib, datetime as dt, websocket
app, table, out = sys.argv[1], sys.argv[2], sys.argv[3]
ws = websocket.create_connection(f"wss://awsedap.epa.gov/public/app/{app}", timeout=120,
        header=["Origin: https://awsedap.epa.gov"], sslopt={"cert_reqs": ssl.CERT_REQUIRED})
mid = 0
def call(method, handle, params):
    global mid; mid += 1
    ws.send(json.dumps({"jsonrpc":"2.0","id":mid,"method":method,"handle":handle,"params":params}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid:
            if "error" in r: raise RuntimeError(r["error"])
            return r["result"]
call("OpenDoc", -1, [app])
meta = call("GetTablesAndKeys", 1, [{"qcx":1000,"qcy":1000},{"qcx":0,"qcy":0},30,True,False])
t = [x for x in meta["qtr"] if x["qName"] == table][0]
fields = [f["qName"] for f in t["qFields"]]; n = t["qNoOfRows"]
lm = call("GetAppLayout", 1, [])["qLayout"]
print("app last reload:", lm.get("qLastReloadTime"), "title:", lm.get("qTitle"))
rows = []
step = 900
for off in range(0, n, step):
    r = call("GetTableData", 1, [off, min(step, n-off), False, table])
    for row in r["qData"]:
        rows.append([c.get("qText") for c in row["qValue"]])
assert len(rows) == n, (len(rows), n)
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(fields); w.writerows(rows)
print("rows", len(rows), "fields", fields)
json.dump({"app": app, "table": table, "rows": n, "fields": fields, "app_last_reload": lm.get("qLastReloadTime"),
           "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "sha256": hashlib.sha256(open(out,"rb").read()).hexdigest()}, open(out + ".meta.json","w"), indent=1)
