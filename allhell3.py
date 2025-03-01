# A_n_g_e_l_a June:2024
# Version for all browsers Firefox, Chrome and Edge.
# Uses a code fragment from Obo on Videohelp which is rather novel.
# The method of taking the browser's license request and just swapping their cdm challenge for ours,
# leaving other stuff as is, seems  to be very powerful, with potentially wide application.

"""
    Effectively this is the grown-up version of l3.py with inputs of mpd and cURL of license URL. If no pssh is found in the mpd then 
    it will either generate one from the Default_KID in the mpd. Or in rare cases if no Default _Kid is found 
    in the mpd, then it will download an init.m4f - the first video fragment - and extract the PSSH from it. 

    Retrieves the keys from a license server using the provided mpd and cURL of the license URL.
    Args:
        mpd (url): The PSSH (Protection System Specific Header) of the content is extracted from the MPD url.
        cURL of licence (str): The cURL of the license server request.
    Returns:
        str: A string containing the keys in the format "--key <kid>:<key>".
        str: A string of the N_m3u8DL-RE command for command line use.
        list: A list of strings of the N_m3u8DL-RE command for python process.run() use
    Optional:    .
    Runs: N_m3u8DL-RE command to download the video.
    Raises:
        httpx.HTTPStatusError: If the HTTP request to the license server fails.
    """

# uses N_m3u8DL-RE, ffmpeg, mkvmerge and mp4decrypt 
# see https://github.com/nilaoda/N_m3u8DL-RE
# see https://www.videohelp.com/software/ffmpeg
# see https://www.videohelp.com/software/MKVToolNix
# see https://www.bento4.com/downloads/

from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
import base64
from base64 import b64encode
import httpx
import re
import urllib.parse
import codecs
import xml.etree.ElementTree as ET
import subprocess
import os
from pathlib import Path
from termcolor import colored
import pyfiglet as PF
import sys
import json
import re

# Append your local bin directory to the PATH
bin_path = os.path.join(os.getcwd(), "bin")
os.environ["PATH"] += os.pathsep + bin_path

####################
#BE SURE TO EDIT THIS to use a different WVD !!!!
####################

WVD_PATH = "./device.wvd"

global header, data

# Widevine System ID
WIDEVINE_SYSTEM_ID = 'EDEF8BA9-79D6-4ACE-A3C8-27DCD51D21ED'

def fetch_mpd_content(url):
    response = httpx.get(url)
    response.raise_for_status()  # Ensure we notice bad responses
    return response.text

def find_default_kid_with_regex(mpd_content):
    # Regular expression to find cenc:default_KID
    match = re.search(r'cenc:default_KID="([A-F0-9-]+)"', mpd_content)
    if match:
        return match.group(1)
    return None

def extract_or_generate_pssh(mpd_content):
    # Parse the MPD content using ElementTree
    # deal with:-
    #       the cenc namespace varitions
    #       the default_KID ``
    # Provide a regex fallback
    try:
        tree = ET.ElementTree(ET.fromstring(mpd_content))
        root = tree.getroot()

        # Namespace map to handle the cenc namespace
        namespaces = {
            'cenc': 'urn:mpeg:cenc:2013',
            '': 'urn:mpeg:dash:schema:mpd:2011'
        }

        # Extract cenc:default_KID using XML parsing
        default_kid = None
        for elem in root.findall('.//ContentProtection', namespaces):
            scheme_id_uri = elem.attrib.get('schemeIdUri', '').upper()
            if scheme_id_uri == 'URN:MPEG:DASH:MP4PROTECTION:2011':
                default_kid = elem.attrib.get('cenc:default_KID')
                if default_kid:
                    print(f"Found default_KID using XML parsing: {default_kid}")
                    break

        # If default_kid is not found using XML parsing, use regex
        if not default_kid:
            default_kid = find_default_kid_with_regex(mpd_content)
            if default_kid:
                print(f"Found default_KID using regex: {default_kid}")

        # Extract Widevine cenc:pssh
        pssh = None
        for elem in root.findall('.//ContentProtection', namespaces):
            scheme_id_uri = elem.attrib.get('schemeIdUri', '').upper()
            if scheme_id_uri == f'URN:UUID:{WIDEVINE_SYSTEM_ID}':
        
                pssh_elem = elem.find('cenc:pssh', namespaces)
                if pssh_elem is not None:
                    pssh = pssh_elem.text
                    print(f"Found pssh element: {pssh}")
                    break

        if pssh is not None:
            return pssh
        elif default_kid is not None:
            # Generate pssh from default_kid
            default_kid = default_kid.replace('-', '')
            s = f'000000387073736800000000edef8ba979d64acea3c827dcd51d21ed000000181210{default_kid}48e3dc959b06'
            return b64encode(bytes.fromhex(s)).decode()
        else:
            # No pssh or default_KID found
            try:
                pssh = get_pssh_from_mpd(mpd_url)  # init.m4f method
            except:
                return None

    except ET.ParseError as e:
        try:
            pssh = get_pssh_from_mpd(mpd_url)  # init.m4f method
            return pssh
        except:
            pass
        print(f"Error parsing MPD content: {e}")
        return None


    except httpx.HTTPError as e:
        print(f"Error fetching MPD content: {e}")
        return None

    
def get_key(pssh, license_url):
    """
    Retrieves a license key for a given PSSH and license URL.

    Args:
        pssh (str): The PSSH value.
        license_url (str): The URL of the license server.

    Returns:
        str: A string containing the license keys, separated by newlines.

    Raises:
        httpx.HTTPStatusError: If there is an HTTP status error while making the request.

    Note:
        This function uses the Cdm class to interact with the device and retrieve the license key.
        It first calls the `get_license_challenge` method of the Cdm instance to obtain the challenge.
        If the `data` parameter is not None, it modifies the challenge based on the pattern found in `data`.
        It then prepares the payload by using the modified challenge or the original challenge if `data` is None.
        The payload is sent to the license server using an HTTP POST request.
        The response content is then parsed to extract the license content
        The license content is then parsed using the `parse_license` method of the Cdm instance.
        The `get_keys` method of the Cdm instance is then used to retrieve the license keys.
        The license keys are returned as a string separated by newlines.
    """
    device = Device.load(WVD_PATH)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()

    challenge = cdm.get_license_challenge(session_id, PSSH(pssh))

    if data:
        # deal with sites that need to return data with the challenge
        if match := re.search(r'"(CAQ=.*?)"', data):  # fix for windows
            challenge = data.replace(match.group(1), base64.b64encode(challenge).decode())
        elif match := re.search(r'"(CAES.*?)"', data):
            challenge = data.replace(match.group(1), base64.b64encode(challenge).decode())
        elif match := re.search(r'=(CAES.*?)(&.*)?$', data): 
            b64challenge = base64.b64encode(challenge).decode()
            quoted = urllib.parse.quote_plus(b64challenge)
            challenge = data.replace(match.group(1), quoted)

    # Prepare the final payload
    payload = challenge if data is None else challenge
 
    license_response = httpx.post(url=license_url, data=payload, headers=headers)
    try:
        license_response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise e

    license_content = license_response.content
    try:
        # if content is returned as JSON object:
        match = re.search(r'"(CAIS.*?)"', license_response.content.decode('utf-8'))
        if match:
            license_content = base64.b64decode(match.group(1))
    except:
        pass

    # Ensure license_content is in the correct format
    if isinstance(license_content, str):
        license_content = base64.b64decode(license_content)

    cdm.parse_license(session_id, license_content)

    keys = []
    for key in cdm.get_keys(session_id):
        if key.type == 'CONTENT':
            keys.append(f"--key {key.kid.hex}:{key.key.hex()}")

    cdm.close(session_id)
    return "\n".join(keys)


def parse_curl(curl_command):
    """
    Parse a cURL command and extract the URL, HTTP method, headers, and data.

    Parameters:
    curl_command (str): The cURL command string.

    Returns:
    tuple: A tuple containing the URL, method, headers (as a dictionary), and data.
    """
    # Extract URL
    url_match = re.search(r"curl\s+(?:-X\s+\w+\s+)?'([^']+)'", curl_command)
    url = url_match.group(1) if url_match else ""
    print(f"URL: {url}")

    # Extract method
    method_match = re.search(r"-X\s+(\w+)", curl_command)
    method = method_match.group(1) if method_match else "UNDEFINED"
    print(f"Method: {method}")

    # Extract headers
    headers = {}
    headers_matches = re.findall(r"-H\s+'([^:]+):\s*(.*?)'", curl_command)
    for header in headers_matches:
        headers[header[0]] = header[1]
    print(f"Headers: {headers}")

    # Extract data
    data_match = re.search(r"--data(?:-raw)?\s+(?:(\$?')|(\$?{?))(.*?)'", curl_command, re.DOTALL)
    if data_match:
        raw_prefix = data_match.group(1)
        data = data_match.group(3)
        if raw_prefix and raw_prefix.startswith('$'):
            data = None
        else:
            # Replace escaped sequences if needed
            data = data.replace('\\\\', '\\').replace('\\x', '\\\\x')
            #print(f"Escaped Data: {data}")
            # Decode the escaped sequences
            try:
                data = codecs.decode(data, 'unicode_escape')
                #print(f"Decoded Data: {data}")
            except Exception as e:
                print(f"Error decoding data: {e}")
                data = ""
    else:
        data = ""
    print(f"Data: {data}")

    return url, method, headers, data

# deal with getting pssh from init.m4f as last resort

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
    print('Extracting PSSHs from init file:', file_path)
    return to_pssh(Path(file_path).read_bytes())

def get_pssh_from_mpd(mpd: str):

    print("Extracting PSSH from MPD...")

    yt_dl = 'yt-dlp'
    init = 'init.m4f'

    files_to_delete = [init]

    for file_name in files_to_delete:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"{file_name} file successfully deleted.")

    try:
        subprocess.run([yt_dl, '-q', '--no-warning', '--test', '--allow-u', '-f', 'bestvideo[ext=mp4]/bestaudio[ext=m4a]/best', '-o', init, mpd])
    except FileNotFoundError:
        print("yt-dlp not found. Trying to download it...")
        subprocess.run(['pip', 'install', 'yt-dlp'])
        import yt_dlp
        
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]/bestaudio[ext=m4a]/best',
            'allow_unplayable_formats': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'no_warnings': True,
            'quiet': True,
            'outtmpl': init,
            'no_merge': True,
            'test': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            url = info_dict.get("url", None)
            if url is None:
                raise ValueError("Failed to download the video")
            video_file_name = ydl.prepare_filename(info_dict)

    pssh_list = extract_pssh_from_file('init.m4f')
    pssh = None
    for target_pssh in pssh_list:
        if 20 < len(target_pssh) < 220:
            pssh = target_pssh

    print(f'\n{pssh}\n')
    # with open("pssh.txt", "a") as f:
        # f.write(f"{pssh}\n {mpd}\n")    


    for file_name in files_to_delete:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"{file_name} file successfully deleted.")
    return pssh

def get_hidden_input(prompt):
    if sys.platform.startswith('win'):
        import msvcrt
        def getch():
            return msvcrt.getch().decode('utf-8')
    else:   
        import tty
        import termios
        def getch():
            """
            Get a single character from the standard input without waiting for the enter key. Linux version.

            This function sets the terminal to raw mode, reads a single character from the standard input,
            and then restores the previous terminal settings. And repeats until ctrl+D. 
            It parses as it reads and removes line returns and escape characters.

            Returns:
                str: The single character read from the standard input.

            Raises:
                None.

            """
            fd = sys.stdin.fileno()

            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

    print(prompt, end="", flush=True)
    input_lines = []
    current_line = ""
    while True:
        ch = getch()
        if ch == '\x04' or ch == '\x1a':  # End of Transmission (Ctrl+D or Ctrl+Z)
            break
        if ch == '\\\n' or ch == '\\\r' or ch == '\\':
            input_lines.append(current_line)
            current_line = ""
            print()  # move to the next line after input
        else:
            current_line += ch
    input_lines.append(current_line)  # ensure --data-raw is captured
    return " ".join(input_lines)

def load_config(json_file):
    """Load configuration from the given JSON file."""
    try:
        with open(json_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading JSON config: {e}")
        sys.exit(1)

    try:
        mpd_url = config["manifestUrl"]
        curl_request = config["licenseCurl"]
        video = config["title"]
    except KeyError as e:
        print(f"Missing key in config: {e}")
        sys.exit(1)

    # Read the deleteMe flag, defaulting to False if not present.
    delete_json = config.get("deleteMe", False)
    return mpd_url, curl_request, video, delete_json

if __name__ == "__main__":
    # Initialize variables
    mpd_url = cURL = video = None
    delete_json = False  # default value

    title = PF.figlet_format(' allhell3 ', font='smslant')
    print(colored(title, 'green'))
    strapline = "A Generic L3 Downloader:\n"
    print(colored(strapline, 'red'))
    strapline = "For DRM content only.\n"
    print(colored(strapline, 'red'))
    strapline = "!!This version is for ALL browsers!!.\n\n"
    print(colored(strapline, 'cyan'))
    # Check if a JSON config file was provided
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        mpd_url, cURL, video, delete_json = load_config(config_file)
    else:
        print('Prepare three inputs.\n 1. MPD URL\n 2. cURL of license server request\n 3. Video name\n\n')

    if not mpd_url:
        mpd_url = input("MPD URL? ")
    mpd_content = fetch_mpd_content(mpd_url)
    if (mpd_content):
        pssh = extract_or_generate_pssh(mpd_content)
        print("Extracted or generated PSSH:", pssh)
    else:
        print("Failed to fetch or parse MPD content.")

    # get cURL from user
    print("Next.\n1. Paste your cURL of license request.\n2. Press Ctrl-D (Linux) or Ctrl-Z (Windows) to save it.")

    # multi OS support for getting hidden multi-line input from different browsers
    if not cURL:
        cURL = get_hidden_input("cURL? ")

    # extract license URL, method, headers, and data
    lic_url, method, headers, data =  parse_curl(cURL)
    # get key from pssh and license URL
    key_results = get_key(pssh, lic_url)
    print('\n' + key_results + '\n')
    # ask user for video name
    if not video:
        video = input("Save Video as? ")
    # use N_m3u8DL-RE to download video provide the  command
    print(f"\nN_m3u8DL-RE '{mpd_url}' {key_results} --save-name {video} -M:format=mkv:muxer=mkvmerge")
    # Split key_results into lines and then split each line into components
    key_components = []
    for line in key_results.strip().split('\n'):
        # Split each line by spaces and add the components to the key_components list
        key_components.extend(line.split())

    # Build the command list
    m3u8dl = 'N_m3u8DL-RE'
    command = [
        m3u8dl,  # The command to run
        mpd_url,          # First argument
        *key_components, # Unpack key_components list into individual arguments
        '--save-name',  # Additional fixed argument
        video,   # Value for the save-name argument
        #'--save-dir',  # uncomment and add save path in quotes
        #'C:/Users/User/Downloads/',  # Value for the save-dir argument
        '-M',  # Additional fixed argument  to mux 
        'format=mkv:muxer=mkvmerge',  # Value for the format argument may also be mp4
    ]
    print(f"\n{command}\n")
    input("Press Enter to run the download-command or ctrl+C to exit.")
    subprocess.run(command)

    # If the json configuration file has "deleteMe" set to True, delete the file.
    if delete_json and config_file:
        try:
            os.remove(config_file)
            print(f"Configuration file '{config_file}' deleted.")
        except Exception as e:
            print(f"Failed to delete configuration file: {e}")
