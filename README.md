# HellYes #

## A Widevine Downloader with multi-browser support for Linux and Windows ##
======================================================================

### Overview


- [A Widevine Downloader with multi-browser support for Linux and Windows](#a-widevine-downloader-with-multi-browser-support-for-linux-and-windows)
- [Pre Use Instructions](#pre-use-instructions)
- [Binaries Installation by hand](#binaries-installation-by-hand)
- [Binaries Installation By Script](#binaries-installation-by-script)
- [Installation for Windows Bare Machine](#installation-for-windows-bare-machine)
- [Installation for Linux](#installation-for-linux)
- [How to Use](#how-to-use)
	- [You Provide](#you-provide)
	- [You Find](#you-find)
	- [Allhell3 In action](#allhell3-in-action)
	- [Allhell gui In action](#allhell-gui-in-action)

A generic L3 downloader for DRM content which comes in two versions

*   allhell3.py
*   gui.py

Allhell3.py is coded for the all browsers (tested on Chrome, Firefox and Edge) and is supplied very nearly ready to download all media protected by widevine.
You just need to provide a working Content Decryption Module and call it device.wvd and place it in the top level folder of HellYes. 

gui.py is the latest Graphical User Interface version of allhell3.py.
gui.py will start after install by 'uv run gui.py'.  Start the command-line versions with 'uv run allhell3.py'.

  
In use, the style of entering data is a little different. allhell3.py uses a paste _without echo to the screen_, and uses Ctrl+D (Linux) or Ctrl+Z (Windows) to signal the end of the cURL input.  
hellyes or gui.py uses a paste _with echo to the screen_, and uses button clicks to process data.  
Use whichever you like best on your system....  
In both versions a downloader (N\_m3u8DL-RE) or Dash-mpd-cli may be used to download the media. Note that the dash-mpd-cli downloader will download subtitles as a separate file and it will NOT be muxed with the video.


You will need you to download some helper software.

### Pre Use Instructions

Install the following either by hand of by using the install scipts provided:

*Note the install scripts will install all the below binaries*

### Binaries Installation by hand ###

*   See the code at [https://github.com/nilaoda/N\_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE), download the latest release. Unzip and save to a folder named 'binaries'. It can be anywhere on your system. So long as 'binaries' is in your Path.
* s See the code at [https://github.com/emarsden/dash-mpd-cli/releases] for details of dash-mpd-cli downloader.
*   Do the same with [ffmpeg](https://www.videohelp.com/software/ffmpeg) and [MKVToolNix](https://www.videohelp.com/software/MKVToolNix) etc.
*   See [https://www.videohelp.com/software/ffmpeg](https://www.videohelp.com/software/ffmpeg) for more information about ffmpeg.
*   See [https://www.videohelp.com/software/MKVToolNix](https://www.videohelp.com/software/MKVToolNix) for more information about MKVToolNix.
*   See [https://www.bento4.com/downloads/](https://www.bento4.com/downloads/) for more information about Bento4.
*   Since allhell3.py is a python script you also need [python or get it from Microsoft Store if on Windows](https://www.python.org/downloads/)

uv is the package manager for HellYes

If you do not alrealy have uv as a python package try to install it first, using pip -  

```
pip install uv
or
python3 -m pip install uv
or use your system's package manager to install python-uv
```
If the uv install fails then use one of the methods described here:- https://docs.astral.sh/uv/getting-started/installation/

### Binaries Installation By Script ###

Install HellYes; 

the following installs and runs the latest version directly from the GitHub repository:

```shell
git clone https://github.com/vinefeeder/HellYes.git
cd HellYes
uv lock
uv sync
uv run gui.py
or 
uv run allhell3.py
```

### Installation for Windows Bare Machine ###  
and novice user.
	
You are going to install all the required binary files and automatically add then to system variable - Path.  The Python interpreter will be installed automatically too.


	- download git from https://github.com/git-for-windows/git/releases/download/v2.52.0.windows.1/Git-2.52.0-64-bit.exe  and run the installer
	- re-start your machine
	- Open Start
	- Type PowerShell and select open PowerShell
	- Within PowerShell change directory, chdir, or cd, to your chosen location, where HellYes is to be installed, and type the following command followed by enter,
	
		
```
git clone https://github.com/vinefeeder/HellYes.git
```

	
	- Files will be downloaded, a folder called HellYes will be created.
	- Close PowerShell and re-open with *admininstrator privileges*. Do...
	- Open Start
	- Type PowerShell
	- Right-click Windows PowerShell → Run as administrator
	- Inside PowerShell, change directory to HellYes (cd HellYes) and run the following command by copying or typing the line, followed by pressing enter.
	
	
```
 powershell -ExecutionPolicy Bypass -File .\Install-media-tools.ps1
```

	
	- Watch the installation, a number of binary files will be downloaded and installed to C:\Tool\bin. Installation will take a while. After finishing, close PowerShell and restart your machine.
	- Open Start
	- Type PowerShell
	- Type uv [return]. Expect to see a screen of help.  If uv did not install from the Install-media-tools.ps1 script you will not see any response. Uv is a python package manager.
	- If uv is not installed close PowerShell and re-open as administrator, so 
	- Open Start
	- Type PowerShell
	- Right-click Windows PowerShell → Run as administrator	
	- Type powershell -ExecutionPolicy Bypass -c "irm https://github.com/astral-sh/uv/releases/download/0.9.18/uv-installer.ps1 | iex" [return]

	- Close PowerShell and re-start your machine.
	- Type [WindowsKey]+R to open PowerShell, 
	- cd to HellYes and type each line below followed by return. Some commands will take a while to finish.
	  	
```
	uv lock
	uv sync  
	uv run gui.py
	or
	uv run hell3.py
	
```
That's it for Windows; uv run gui.py to get started!  

### Installation for Linux ###
with a bare machine.

There is an installation file to install binaries. Install-media-tools.sh. Open it in a text editor and edit lines 6 and 7. Change the Debian/Ubuntu package-manager command 'apt-get' to whatever your package manager uses (dnf, pacman, yast, etc)  
Then save and close and run the script with 
```
sudo bash ./Install-media-tools.sh
```
The script will take some time to install. Check uv is installed.
If not, you can install uv with the following command in a terminal window

```
wget -qO- https://astral.sh/uv/install.sh | sh
```
Finally, cd to HellYes and run each command in order,

```
	uv lock
	uv sync  
	uv run gui.py
	or
	uv run allhell3.py
```

  
That's it; uv run hellyes to get started!  

### How to Use  

You provide three bits of information taken from a web page and hellyes or any of the allhell3.py family of scr does the rest.

You start the python script with 'uv run hellyes'  - written in a terminal.

#### You Provide

*   MPD URL
*   cURL of license server request
*   Video name

After you provide the data, it will download the video using N\_m3u8DL-RE or dash-mpd-cli, should you wish, finding keys in the process.

#### You Find

*   MPD URL

Copy and paste the MPD URL from the web page.

![Example of mpd and license URL](images/selected_mpd_license.png)

For example, open this image in a new tab to see it full size.

The image shows the MPD URL as the first entry. How would we know it was the right one? it has mpd written in it.

How did we open that tool in the browser? Press ctrl+shift+C

How did we hide all the other stuff a web page loads? We used a filter

![Example with filter](images/filter.png)

The filter is a regex or regular expression - it's a way of saying "find all the lines that contain mpd and license"

the regex is "regexp:widevine|acquire|license|mpd" and it means "find all the lines that contain widevine or acquire or license or mpd". However, Chrome does not allow regexp: so use a single word like license or mpd etc.

With experience you will learn that sites use different words to identify their license url.  
And if the filter does not find anything, search with method:POST as a filter. POST messages are sent securely, most http traffic isn't. But licenses are.

*   cURL of license server request

Copy and paste the cURL of the license server request.

For example, open this image in a new tab to see it full size.

![Example of curl](images/selected_cURL.png)

Which 'copy as cURL' to use? Windows - choose 'Copy as cURL (Posix)' if available or 'Copy as cURL (bash)'

If using allhell3.py terminate your paste command and tell the script to process the cURL by using Ctrl+Z (Windows) or Ctrl+D (Linux).  
Be prepared for the screen to write several blank lines, shifting existing text upwards rapidly.

*   Video name

Video name is requested once keys are found and the script is ready to download. The name does not need a file type extension added.

Your file will be downloaded to the HellYes folder.


#### Allhell3 In action

Running the script. ![Example pasting mpd](images/enter_mpd.png) ![curl pastes to screen with echo and finds keys](images/keys.png)

Note carefully: allhell3.py.py uses Ctrl + D to enter the cURL on Linux and Ctrl + Z on Windows. Nothing prints to the screen until Ctrl+D or Z is pressed.

#### Allhell gui In action

![Starting GUI](images/gui2.png) ![Populating Data](images/gui3.png) ![N_m3u8DL-RE running in terminal](images/gui4.png) ![New Gui with reset and dash-mpd-cli download](images/gui5.png)


Happy allhell3!  
 
A\_n\_g\_e\_l\_a
