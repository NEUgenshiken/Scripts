from dataclasses import dataclass
import requests
import subprocess
import fire
import os, re, time

@dataclass(frozen=True)
class EnvArgs:
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.47"
    tracker_list_url: str = "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt"
    proxy: str = "http://127.0.0.1:7890"
    curdir: str = os.getcwd()
    aria2c: str = "D:\\Projects\\aria2\\aria2c.exe"
    qbittorrent: str = "D:\\sfw\\qBittorrent\\qbittorrent.exe"
    torfolder: str = f"{curdir}\\torrents"

env = EnvArgs()

@dataclass(frozen=True)
class Aria2Args:
    default_params = (
        f"--dir={env.torfolder}",
        "--max-concurrent-downloads=5",
        "--max-connection-per-server=16",
        "--split=64",
        "--continue=true",
        f"--user-agent=\"{env.user_agent}\"",
        "--summary-interval=0",
        "--disk-cache=64M",
        "--file-allocation=none",
        "--no-file-allocation-limit=64M",
        "--auto-save-interval=20",
        "--http-accept-gzip=true",
        "--auto-file-renaming=true",
        "--content-disposition-default-utf8=true",
    )
    proxy_params: list[str] = (
        f"--all-proxy={env.proxy}",
    )
    bt_params: list[str] = (
        "--enable-dht6=true",
        "--bt-metadata-only=true",
        "--bt-save-metadata=true",
    )

aria2 = Aria2Args()


def check_tracker_need_update(path: str) -> bool:
    if not os.path.exists(path):
        return False
    last_modified = time.localtime(os.path.getmtime(path))
    ymd = time.strftime(r"%Y%m%d", last_modified)
    cur = time.strftime(r"%Y%m%d", time.localtime())
    return ymd != cur


def tracker_list() -> list[str]:
    tracker_file = ".trlst"
    if check_tracker_need_update(tracker_file):
        with open(tracker_file, "r") as trlst:
            return [s for s in trlst.readlines() if len(s.strip()) > 0]
    response = requests.get(
        url=env.tracker_list_url,
        proxies={
            "http": env.proxy,
            "https": env.proxy,
        }
    )
    lines = response.text.split("\n\n")
    with open(tracker_file, "w") as trlst:
        for tr in lines:
            if len(tr) > 0:
                trlst.write(f"{tr}\n")
    return lines


def add_tracker_info(maglink: str, trackers: list[str]) -> str:
    if len(maglink.strip()) < 21:
        raise Exception("magnet link not long enough")
    tr = str()
    for s in trackers:
        if len(s.strip()) > 0:
            tr = f"{tr}&tr={s}"
    return f"{maglink}{tr}"


def extract_hash(maglink: str) -> str:
    caps = re.search(r"magnet:\?xt=urn:btih:([0-9a-zA-Z]*).*", maglink)
    return caps.group(1)


def main(maglink: str):
    maglink = maglink.strip()
    trackers = tracker_list()
    torrent = f"{env.torfolder}\\{extract_hash(maglink)}.torrent"
    maglink = add_tracker_info(maglink, trackers)
    cmd = [
        env.aria2c, maglink,
        *aria2.default_params,
        *aria2.proxy_params,
        *aria2.bt_params,
    ]
    subprocess.run(cmd, check=True)

    # call qbittorrent
    cmd = [
        env.qbittorrent, torrent
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    fire.Fire(main)