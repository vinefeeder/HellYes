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

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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
    if isinstance(hdrs_raw, str):                 # backward-compat for old files
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

def find_wv_pssh_offsets(raw: bytes) -> list:
    offsets = []
    offset = 0
    while True:
        offset = raw.find(b'pssh', offset)
        if offset == -1:
            break
        size = int.from_bytes(raw[offset-4:offset], byteorder='big')
        pssh_offset = offset - 4
        offsets.append(raw[pssh_offset:pssh_offset+size])
        offset += size
    return offsets

def to_pssh(content: bytes) -> list:
    wv_offsets = find_wv_pssh_offsets(content)
    return [base64.b64encode(wv_offset).decode() for wv_offset in wv_offsets]

def extract_pssh_from_file(file_path: str) -> list:
    return to_pssh(Path(file_path).read_bytes())

def get_pssh_from_mpd(mpd_url):
    print(colored("DEBUG: Attempting to extract PSSH via fragment (yt-dlp)...", "magenta"))
    init = "init.m4f"
    if os.path.exists(init): os.remove(init)

    try:
        subprocess.run([
            'yt-dlp', '-q', '--no-warning', '--test', '--allow-u',
            '-f', 'bestvideo[ext=mp4]/bestaudio[ext=m4a]/best',
            '-o', init, mpd_url
        ], check=True)
    except Exception as e:
        print(colored(f"WARN: yt-dlp failed: {e}", "yellow"))
        return None

    if not os.path.exists(init):
        return None

    pssh_list = extract_pssh_from_file(init)
    os.remove(init)

    for p in pssh_list:
        if 20 < len(p) < 220:
            return p
    return None

def extract_or_gen_pssh(mpd_url, mpd_text):
    ns = {'cenc':"urn:mpeg:cenc:2013", '':"urn:mpeg:dash:schema:mpd:2011"}
    try:
        root = ET.fromstring(mpd_text)
        # Widevine <ContentProtection>
        for cp in root.findall(".//ContentProtection", ns):
            if cp.attrib.get("schemeIdUri","").upper() == f"URN:UUID:{WIDEVINE_SYSTEM_ID}":
                pssh_elem = cp.find("cenc:pssh", ns)
                if pssh_elem is not None:
                    return pssh_elem.text.strip()
    except Exception:
        pass

    # fallback 1: default_KID
    kid = find_default_kid(mpd_text)
    if kid:
        print(colored(f"DEBUG: Generating PSSH from default_KID: {kid}", "magenta"))
        kid = kid.replace("-","")
        blob = f"000000387073736800000000edef8ba979d64acea3c827dcd51d21ed000000181210{kid}48e3dc959b06"
        return base64.b64encode(bytes.fromhex(blob)).decode()

    # fallback 2: download fragment
    pssh = get_pssh_from_mpd(mpd_url)
    if pssh:
        return pssh

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
    print(colored(f"DEBUG: Challenge generated ({len(challenge)} bytes)", "magenta"))

    # ------------ patch the original body -----------------------------------
    # For maximum compatibility with allhell3o.py, we follow the same logic:
    # Try text-based pattern matching first (for JSON/query-string wrapped challenges)
    # Otherwise, send the original body unchanged (for binary protobuf wrappers like Nagra)

    payload_bytes = challenge  # Default: send raw challenge

    try:
        # Try to decode as text to check for base64-encoded challenges
        template = body_bytes.decode("utf-8") if body_bytes else ""

        # Try the 3 patterns seen in some DRM providers (text-based wrappers)
        for pat, urlquote in [
            (r'"(CAQ=.*?)"',        False),          # JSON value
            (r'"(CAES.*?)"',        False),          # JSON value (alt)
            (r'=(CAES.*?)(&|$)',    True),           # query-string
        ]:
            m = re.search(pat, template)
            if m:
                print(colored(f"DEBUG: Text pattern found: {pat}", "magenta"))
                repl = base64.b64encode(challenge).decode()
                if urlquote:
                    repl = urllib.parse.quote_plus(repl)
                patched = template.replace(m.group(1), repl)
                payload_bytes = patched.encode("utf-8")
                break
        else:
            # No text pattern found - send raw challenge (same as allhell3o.py)
            print(colored("DEBUG: No text pattern found. Sending raw challenge.", "magenta"))
            payload_bytes = challenge
    except UnicodeDecodeError:
        # Body is binary and can't be decoded as text - send raw challenge
        print(colored("DEBUG: Binary body. Sending raw challenge.", "magenta"))
        payload_bytes = challenge

    # ------------ prepare headers -------------------------------------------
    hdrs = headers.copy()
    hdrs.pop("Content-Length", None)   # let httpx calculate correct size
    hdrs.pop("Host", None)             # httpx fills it

    # ------------ POST -------------------------------------------------------
    print(colored(f"DEBUG: Sending POST to {url}", "magenta"))
    print(colored(f"DEBUG: Sending challenge via data= parameter ({len(challenge)} bytes)", "magenta"))
    resp = httpx.post(url, headers=hdrs, data=challenge)

    print(colored(f"DEBUG: Response Status: {resp.status_code}", "magenta"))
    if resp.status_code != 200:
        print(colored(f"DEBUG: Error in body: {resp.text[:200]}...", "red"))

    resp.raise_for_status()            # will raise if not 2xx/3xx

    # ------------ parse licence ---------------------------------------------
    content = resp.content
    if (m := re.search(r'"(CAIS.*?)"', resp.text)):
        print(colored("DEBUG: License extracted from JSON field (CAIS...)", "magenta"))
        content = base64.b64decode(m.group(1))

    # Ensure content is bytes (though base64.b64decode and resp.content are bytes)
    if isinstance(content, str):
        content = base64.b64decode(content)

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
        sys.exit("usage: allhell3.py  <json-file-from-extension>")

    mpd, lic_url, headers, body, title, delete_me = load_json_cfg(sys.argv[1])

    pssh = extract_or_gen_pssh(mpd, fetch(mpd))
    print(colored(f"PSSH → {pssh}\n", "cyan"))

    print(colored(f"lic_url → {lic_url}\n", "cyan"))
    print(colored(f"headers → {headers}\n", "cyan"))
    print(colored(f"body → {body}\n", "cyan"))
    keys = get_keys(pssh, lic_url, headers, body)
    print(colored("\n".join(keys) + "\n", "yellow"))

    # Create downloads directory if it doesn't exist
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)

    # Add bin/ to PATH so executables can be found (like /usr/local/bin)
    bin_dir = Path(__file__).parent / "bin"
    env = os.environ.copy()
    env['PATH'] = str(bin_dir.absolute()) + os.pathsep + env.get('PATH', '')

    # Determine executable path based on platform
    if sys.platform == 'win32':
        n_m3u8dl_exe = str(bin_dir / "N_m3u8DL-RE.exe")
    else:
        n_m3u8dl_exe = str(bin_dir / "N_m3u8DL-RE")

    cmd = [
        n_m3u8dl_exe, mpd, *sum((k.split() for k in keys), []),
        "--save-name", title,
        "--save-dir", str(downloads_dir),
        "-M", "format=mkv:muxer=mkvmerge",
        "--auto-select"
    ]
    print(colored(" ".join(cmd) + "\n", "green"))

    input("↩  Enter to run, Ctrl-C to abort … ")
    subprocess.run(cmd, env=env)

    if delete_me:
        os.remove(sys.argv[1])
