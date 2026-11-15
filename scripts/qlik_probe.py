"""Probe a public Qlik Sense app via the Engine JSON-RPC websocket (read-only)."""
import json, sys, ssl, websocket
app = sys.argv[1]
url = f"wss://awsedap.epa.gov/public/app/{app}"
ws = websocket.create_connection(url, timeout=60, header=["Origin: https://awsedap.epa.gov"], sslopt={"cert_reqs": ssl.CERT_REQUIRED})
mid = 0
def call(method, handle, params):
    global mid; mid += 1
    ws.send(json.dumps({"jsonrpc":"2.0","id":mid,"method":method,"handle":handle,"params":params}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid: return r
print(call("OpenDoc", -1, [app]).get("result") or "OPEN FAILED")
r = call("GetTablesAndKeys", 1, [{"qcx":1000,"qcy":1000},{"qcx":0,"qcy":0},30,True,False])
for t in r.get("result",{}).get("qtr",[]):
    print("TABLE", t["qName"], t.get("qNoOfRows"), [f["qName"] for f in t["qFields"]])
if "error" in r: print(r)
