from debug import debug
import sys
import json
from utils import *
import re
from req import *
import threading
import math
from dataclasses import dataclass
import io
from pydub import AudioSegment

CLIENT_ID = "QH0sodO4QzbRjYm1f4FpCtEJvOB3PbaU"
DEFAULT_MAX_WORKERS = 4

req = Req()

class SCVersion:
    def __init__(self):
        try:
            debug("[!] getting soundcloud version...")

            res = req.session.get("https://soundcloud.com/versions.json")
            parsed = json.loads(res.text)
            ver = parsed["app"]

            debug(f"[+] soundcloud version: {ver}")

            self.version = ver
        except Exception as e:
            debug("[-] failed to get soundcloud version")

            print(e)
            sys.exit(-1)

    def __str__(self):
        return self.version

class SCPlaylist:
    def __init__(self, title: str, transcoding_url: str, auth: str):
        try:
            debug(f"[!] getting {title} playlist url")

            pl_url = transcoding_url
            pl_url += "?"
            pl_url += f"client_id={CLIENT_ID}"
            pl_url += "&"
            pl_url += f"track_authorization={auth}"

            res = req.session.get(pl_url)
            parsed = json.loads(res.text)

            debug(f"[+] found playlist url for {title}")

            self.url = parsed["url"]

            self.parse()

        except Exception as e:
            debug(f"[-] failed to get {title} playlist url")

            print(e)
            sys.exit(-1)

    def __len__(self):
        return len(self.links)

    def parse(self) -> list[str]:
        try:
            debug("[!] parsing playlist")

            links = []

            res = req.session.get(self.url)
            text = res.text

            i = text.find("https")
            while i > 0:
                end = text[i:].find("\n")

                link = text[i:i+end]
                if link[-1] == "\"":
                    link = link[:-1]

                links.append(link)

                text = text[i+5:]
                i = text.find("https")

            debug("[+] successfully parsed playlist")

            self.links = links

        except Exception as e:
            debug("[-] failed to parse playlist")

            print(e)
            sys.exit(-1)

@dataclass
class WorkerData:
    idx: int
    part_per_worker: int
    leftovers: int
    is_last: bool

class Worker(threading.Thread):
    def __init__(self, data: WorkerData, track):
        super().__init__(daemon=True)
        self.data = data
        self.track = track
        self.stop_ev = threading.Event()
        self.buffer = io.BytesIO()

    def stop(self):
        self.stop_ev.set()

    def run(self):
        local_req = Req()
        start = self.data.idx * self.data.part_per_worker
        last = start + self.data.part_per_worker
        if self.data.is_last:
            last += self.data.leftovers

        for i in range(start, last, 1):
            if self.stop_ev.is_set():
                return

            debug(f"[!] thread: {self.data.idx}\tattempting to download part {i}")

            res = local_req.session.get(self.track.playlist.links[i])
            self.buffer.write(res.content)
            debug(f"[!] thread: {self.data.idx}\tread {len(res.content)} bytes from part {i}")

        debug(f"[!] thread: {self.data.idx}\tread total {self.buffer.tell()} bytes")
        return

class DLHandle:
    def __init__(self, workers: list[Worker], track):
        self.workers = workers
        self.track = track
        self.buffer = io.BytesIO()

    def join_all(self):
        for worker in self.workers:
            worker.join()

        #with open(self.track.path, "wb") as f:
        #    for worker in self.workers:
        #        f.write(memoryview(worker.buffer.getbuffer()))

        self.buffer = io.BytesIO(b"".join(w.buffer.getvalue() for w in self.workers))

        audio = AudioSegment.from_file(self.buffer, format="mp4")
        audio.export(self.track.path, format="mp3")

        print(f"[+] saved {self.track.title} in {self.track.path}")

class SCTrack:
    def __init__(self, _id: int, url: str, title: str, duration: int, transcoding_url: str, auth: str):
        self.url = url
        self.title = title
        self.duration = duration
        self._id = _id
        self.transcoding_url = transcoding_url
        self.auth = auth

    @staticmethod
    def from_url(url: str):
        url = f"https://api-v2.soundcloud.com/resolve?url={url}&client_id={CLIENT_ID}"
        res = req.session.get(url)
        parsed = json.loads(res.text)
        return SCTrack.from_sc_response(parsed)

    @staticmethod
    def from_sc_response(track: dict):
        return SCTrack(
            _id=track["id"],
             url=track["permalink_url"],
            title=track["title"],
            duration=track["media"]["transcodings"][0]["duration"],
            transcoding_url=track["media"]["transcodings"][0]["url"],
            auth=track["track_authorization"]
        )

    def prepare(self):
        self.playlist = SCPlaylist(self.title, self.transcoding_url, self.auth)

    def prepare_trackname(self, o_dir: str) -> str:
        safe_track_name = re.sub(r"[\\/]", "-", self.title)
        return f"{o_dir}/{safe_track_name}.mp3"

    def download(self, o_dir: str):
        try:
            self.prepare()

            debug(f"downloading {self.title}")

            self.path = self.prepare_trackname(o_dir)

            with open(self.path, "wb") as f:
                for index, link in enumerate(self.playlist.links):
                    res = req.session.get(link)
                    for chunk in res.iter_content(chunk_size=8192):
                        f.write(chunk)

            debug(f"[+] {self.title} saved to {self.path}")

        except Exception as e:
            debug(f"[!] failed to download {self.title}")

            print(e)
            sys.exit(-1)

    def download_parallel(self, o_dir: str, part_per_worker: int=-1, max_workers: int=DEFAULT_MAX_WORKERS) -> DLHandle:
        try:
            self.prepare()

            debug(f"downloading {self.title}")

            self.path = self.prepare_trackname(o_dir)
            workers = []
            pl_len = len(self.playlist)

            if part_per_worker <= 0:
                n_workers = max_workers
                part_per_worker = math.floor(pl_len / n_workers)
            else:
                n_workers = math.floor(pl_len / part_per_worker)
                if n_workers > max_workers:
                    n_workers = max_workers
                    part_per_worker = math.floor(pl_len / n_workers)

            leftovers = pl_len % part_per_worker

            print("pl_len: ", pl_len)
            print("n_workers: ", n_workers)
            print("leftovers: ", leftovers)
            print("part_per_worker: ", part_per_worker)

            for worker_id in range(n_workers):
                data = WorkerData(worker_id, part_per_worker, leftovers, worker_id == n_workers-1)
                worker = Worker(data, self)
                worker.start()
                workers.append(worker)

            return DLHandle(workers, self)

            # join downloaded data
            # write to file
            # additionally make a way for dumping downloaded data once a while so ram doesnt explode

        except Exception as e:
            debug(f"[!] failed to download parallel {self.title}")

            print(e)
            sys.exit(-1)

class SCUser:
    def __init__(self, username: str):
        self.username = username

        try:
            debug(f"[!] getting soundcloud userid for {self.username}")

            res = req.session.get(f"https://api-v2.soundcloud.com/resolve?url=https://soundcloud.com/{username}&client_id={CLIENT_ID}")
            parsed = json.loads(res.text)
            self.userid = parsed["id"]

            debug(f"[+] {self.username} is {self.userid}")

        except Exception as e:
            debug(f"[!] failed to get userid for {self.username}")

            print(e)
            sys.exit(-1)

    def get_tracks(self, limit: int) -> list[SCTrack]:
        try:
            debug(f"[!] trying to get {self.username}'s tracks")

            ts = now_ts()
            ver = SCVersion()
            url = f"https://api-v2.soundcloud.com/users/{self.userid}/tracks?offset={ts},tracks,00000000000000000000&limit={limit}&representation=&client_id={CLIENT_ID}&app_version={ver}&app_locale=en"

            res = req.session.get(url)
            parsed = json.loads(res.text)
            collection = parsed["collection"]

            debug(f"[+] found {len(collection)} tracks for {self.username}")

            tracks = []
            for track in collection:
                tracks.append(SCTrack.from_sc_response(track))

            return tracks

        except Exception as e:
            debug(f"[-] failed to get tracks for {self.username}")

            print(e)
            sys.exit(-1)
