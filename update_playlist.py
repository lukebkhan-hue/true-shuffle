"""
Refresh the song list built into index.html.

Reads every video in the playlist straight from youtube.com (no API key needed,
playlist must be public or unlisted) and rewrites the JSON block between the
BUILTIN markers in index.html. Run it whenever songs were added or removed:

    python update_playlist.py            # uses the playlist id below
    python update_playlist.py <id-or-url>
"""
import datetime
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PLAYLIST = "PL48ssHKh87zu-zuM-vt6qZgFq0TOQmFum"
INDEX = Path(__file__).resolve().parent / "index.html"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def http(url, data=None, headers=None):
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def walk(node, out):
    """Collect videos + the next continuation token from YouTube's page data (old and new layouts)."""
    if isinstance(node, dict):
        if "playlistVideoRenderer" in node:
            v = node["playlistVideoRenderer"]
            title = "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))
            by = "".join(r.get("text", "") for r in v.get("shortBylineText", {}).get("runs", []))
            out["videos"].append({"id": v.get("videoId"), "title": title, "by": by})
        elif "lockupViewModel" in node:
            v = node["lockupViewModel"]
            if v.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO" and v.get("contentId"):
                md = v.get("metadata", {}).get("lockupMetadataViewModel", {})
                title = md.get("title", {}).get("content", "")
                by = ""
                try:
                    by = md["metadata"]["contentMetadataViewModel"]["metadataRows"][0]["metadataParts"][0]["text"]["content"]
                except (KeyError, IndexError, TypeError):
                    pass
                out["videos"].append({"id": v["contentId"], "title": title, "by": by})
        elif "continuationCommand" in node and "token" in node["continuationCommand"]:
            if node["continuationCommand"].get("request", "CONTINUATION_REQUEST_TYPE_BROWSE") == "CONTINUATION_REQUEST_TYPE_BROWSE":
                out["continuation"] = out["continuation"] or node["continuationCommand"]["token"]
        elif "continuationItemRenderer" in node:
            try:
                out["continuation"] = node["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
            except KeyError:
                pass
        else:
            for val in node.values():
                walk(val, out)
    elif isinstance(node, list):
        for val in node:
            walk(val, out)


def playlist_id_from(text):
    m = re.search(r"[?&]list=([A-Za-z0-9_-]+)", text)
    return m.group(1) if m else text.strip()


def fetch(pid):
    html = http("https://www.youtube.com/playlist?list=" + urllib.parse.quote(pid) + "&hl=en")
    m = re.search(r"ytInitialData\s*=\s*(\{.*?\})\s*;\s*</script>", html, re.S)
    if not m:
        raise SystemExit("Could not read the playlist page. Is the playlist public or unlisted?")
    out = {"videos": [], "continuation": None}
    walk(json.loads(m.group(1)), out)
    title = re.search(r'<meta property="og:title" content="([^"]*)"', html)
    key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
    ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
    pages = 0
    while out["continuation"] and key and pages < 100:
        pages += 1
        body = json.dumps({"context": {"client": {"clientName": "WEB", "clientVersion": ver.group(1) if ver else "2.20240101.00.00",
                                                  "hl": "en", "gl": "US"}},
                           "continuation": out["continuation"]}).encode()
        out["continuation"] = None
        page = http("https://www.youtube.com/youtubei/v1/browse?key=" + key.group(1) + "&prettyPrint=false",
                    data=body, headers={"Content-Type": "application/json"})
        walk(json.loads(page), out)
    seen, videos = set(), []
    for v in out["videos"]:
        if v["id"] and v["id"] not in seen:
            seen.add(v["id"])
            videos.append({"id": v["id"], "title": v["title"] or v["id"], "by": v["by"]})
    if not videos:
        raise SystemExit("No videos found. Is the playlist public or unlisted?")
    return {"id": pid, "title": title.group(1) if title else pid,
            "updated": datetime.date.today().isoformat(), "videos": videos}


def main():
    pid = playlist_id_from(sys.argv[1]) if len(sys.argv) > 1 else PLAYLIST
    data = fetch(pid)
    html = INDEX.read_text(encoding="utf-8")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    new, n = re.subn(r"(<!--BUILTIN-->).*?(<!--/BUILTIN-->)", lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
    if n != 1:
        raise SystemExit("index.html has no BUILTIN markers")
    INDEX.write_text(new, encoding="utf-8")
    print(f'"{data["title"]}": {len(data["videos"])} songs written into {INDEX.name} (updated {data["updated"]})')


if __name__ == "__main__":
    main()
