#!/usr/bin/env python3
# allhell3.py  ·  July 2025  ·  universal browser edition
# ------------------------------------------------------------------------------
# Given:
#   • manifestUrl       – MPEG‑DASH MPD
#   • licenseUrl + headers + bodyBase64 – Widevine licence POST
# Produces:
#   • content keys
#   • ready‑to‑run N_m3u8DL‑RE command
# ------------------------------------------------------------------------------

import base64, httpx, json, os, re, subprocess, sys, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
from termcolor import colored
import pyfiglet as PF

from pywidevine.cdm    import Cdm
from pywidevine.device import Device
from pywidevine.pssh   import PSSH

# ------------------------------------------------------------------------------ config
WVD_PATH            = "./device.wvd"
WIDEVINE_SYSTEM_ID  = "EDEF8BA9-79D6-4ACE-A3C8-27DCD51D21ED"

# ------------------------------------------------------------------------------ helpers
def fetch(url):                              # grab MPD text
    r = httpx.get(url); r.raise_for_status(); return r.text

def load_json_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    mpd_url   = cfg["manifestUrl"]
    lic_url   = cfg["licenseUrl"]
    body_b64  = cfg["bodyBase64"]
    title     = cfg.get("title", "video")
    delete_me = cfg.get("deleteMe", False)

    # --- new  --------------------------------------------------------
    hdrs_raw = cfg.get("headers", {})
    if isinstance(hdrs_raw, str):                 # backward‑compat for old files
        hdrs = dict(re.findall(r"([^:]+):\s*([^;]+)", hdrs_raw))
    else:
        hdrs = hdrs_raw
    # -----------------------------------------------------------------

    body = base64.b64decode(body_b64)
    return mpd_url, lic_url, hdrs, body, title, delete_me

# ---------------------- MPD → PSSH ----------------------------------------------------
def find_default_kid(text):                  # regex fallback
    m = re.search(r'cenc:default_KID="([A-F0-9-]+)"', text)
    return m.group(1) if m else None

def extract_or_gen_pssh(mpd_text):
    ns = {'cenc':"urn:mpeg:cenc:2013", '':"urn:mpeg:dash:schema:mpd:2011"}
    root = ET.fromstring(mpd_text)

    # Widevine <ContentProtection>
    for cp in root.findall(".//ContentProtection", ns):
        if cp.attrib.get("schemeIdUri","").upper() == f"URN:UUID:{WIDEVINE_SYSTEM_ID}":
            pssh_elem = cp.find("cenc:pssh", ns)
            if pssh_elem is not None:
                return pssh_elem.text.strip()

    # else: try default_KID
    kid = find_default_kid(mpd_text)
    if kid:
        kid = kid.replace("-","")
        blob = f"000000387073736800000000edef8ba979d64acea3c827dcd51d21ed000000181210{kid}48e3dc959b06"
        return base64.b64encode(bytes.fromhex(blob)).decode()

    sys.exit("✖ could not find PSSH or default_KID in MPD")

# ---------------------- licence POST  -------------------------------------------------
def get_keys(pssh_b64, url, headers, body_bytes):
    """
    Build a valid licence request by *patching* the browser's original POST
    body with our fresh Widevine challenge, then return the CONTENT keys.
    """
    # ------------ make a challenge ------------------------------------------
    dev   = Device.load(WVD_PATH)
    cdm   = Cdm.from_device(dev)
    ses   = cdm.open()
    challenge = cdm.get_license_challenge(ses, PSSH(pssh_b64))  # bytes

    # ------------ patch the original body -----------------------------------
    # Convert raw bytes to a mutable latin‑1 string (1‑byte → 1‑char)
    template = body_bytes.decode("latin1") if body_bytes else ""
    patched  = None

    # Try the 3 patterns seen in Nagra / Adobe licence blobs
    for pat, urlquote in [
        (r'"(CAQ=.*?)"',        False),          # JSON value
        (r'"(CAES.*?)"',        False),          # JSON value (alt)
        (r'=(CAES.*?)(&|$)',    True),           # query‑string
    ]:
        m = re.search(pat, template)
        if m:
            repl = base64.b64encode(challenge).decode()
            if urlquote:
                repl = urllib.parse.quote_plus(repl)
            patched = template.replace(m.group(1), repl)
            break

    # If none of the patterns matched, fall back to sending the raw challenge
    payload_bytes = patched.encode("latin1") if patched else challenge

    # ------------ prepare headers -------------------------------------------
    hdrs = headers.copy()
    hdrs.pop("Content-Length", None)   # let httpx calculate correct size
    hdrs.pop("Host", None)             # httpx fills it
    hdrs.setdefault("Content-Type", "application/octet-stream")

    # ------------ POST -------------------------------------------------------
    resp = httpx.post(url, headers=hdrs, data=payload_bytes)
    resp.raise_for_status()            # will raise if not 2xx/3xx

    # ------------ parse licence ---------------------------------------------
    content = resp.content
    if (m := re.search(r'"(CAIS.*?)"', resp.text)):
        content = base64.b64decode(m.group(1))

    cdm.parse_license(ses, content)
    keys = [f"--key {k.kid.hex}:{k.key.hex()}"
            for k in cdm.get_keys(ses) if k.type == 'CONTENT']
    cdm.close(ses)
    return keys

# ------------------------------------------------------------------------------ main
if __name__ == "__main__":
    banner = PF.figlet_format(" allhell3 ", font="smslant")
    print(colored(banner, "green"))

    if len(sys.argv) < 2:
        sys.exit("usage: allhell3.py  <json‑file‑from‑extension>")

    mpd, lic_url, headers, body, title, delete_me = load_json_cfg(sys.argv[1])

    pssh = extract_or_gen_pssh(fetch(mpd))
    print(colored(f"PSSH → {pssh}\n", "cyan"))

    keys = get_keys(pssh, lic_url, headers, body)
    print(colored("\n".join(keys) + "\n", "yellow"))

    cmd = [
        "N_m3u8DL-RE", mpd, *sum((k.split() for k in keys), []),
        "--save-name", title,
        "-M", "format=mkv:muxer=mkvmerge"
    ]
    print(colored(" ".join(cmd) + "\n", "green"))

    input("↩  Enter to run, Ctrl‑C to abort … ")
    subprocess.run(cmd)

    if delete_me:
        os.remove(sys.argv[1])
