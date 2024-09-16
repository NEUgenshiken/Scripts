from typing import Any
import toml
import aria2p, requests
import os, time

# clear proxy info
os.environ["all_proxy"] = os.environ["http_proxy"] = os.environ["https_proxy"] = ""

conf = toml.decoder.load("conf/aria2.toml")

aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=conf["rpc-secret"],
    )
)

def check_tracker_need_update(path: str) -> bool:
    if not os.path.exists(path):
        return True
    last_modified = time.localtime(os.path.getmtime(path))
    ymd = time.strftime(r"%Y%m%d", last_modified)
    cur = time.strftime(r"%Y%m%d", time.localtime())
    return ymd != cur


def tracker_list() -> list[str]:
    tracker_file = ".trlst"
    if not check_tracker_need_update(tracker_file):
        with open(tracker_file, "r") as trlst:
            return [s for s in trlst.readlines() if len(s.strip()) > 0]
    response = requests.get(conf["tracker-list"])
    lines = response.text.split("\n\n")
    with open(tracker_file, "w") as trlst:
        for tr in lines:
            if len(tr) > 0:
                trlst.write(f"{tr}\n")
    return lines

if __name__ == "__main__":
    magnet_uri = """  """
    magnet_uri = magnet_uri.strip()
    for tr in tracker_list():
        tr = tr.strip()
        if len(tr) > 0:
            magnet_uri = f"{magnet_uri}&tr={tr}"
    download = aria2.add_magnet(magnet_uri)

