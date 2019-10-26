import os
import subprocess
import urllib.request
import sys
import ctypes
import re
import platform
import tempfile
from io import StringIO
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from shutil import move

# Removes a section from a file, by matching the first/last
# lines of the section.
def remove_section(in_file, out_file, start_pattern, end_pattern):
    """
    Removes a section from a file, by matching the first/last line of the section.

    :param file in_file: The file to read (looking for a section to remove)
    :param file out_file: The file to write to (effectively a copy of in_file)
    :param str start_pattern: A regex expression to match the first line of the section
    :param str end_pattern: A regex expression to match the last line of the section
    """
    inside_section = False
    last_line_of_section = False
    for line in in_file.readlines():
        # Identify if inside section to replace
        if re.match(start_pattern, line):
            inside_section = True
        elif re.match(end_pattern, line):
            inside_section = False
            last_line_of_section = True
        # Echo out line if not inside section to replacecd
        if (not inside_section) and (not last_line_of_section):
            out_file.write(line)
        last_line_of_section = False


def write_wrapper_script(script_file, args):
    if platform.system() == "Linux":
        with open(str(script_file), "w") as out_file:
            out_file.write("#!/bin/bash\n")
            out_file.write("\n")
            for arg in args:
                out_file.write("\"%s\" " % arg)
            # Pass through any script args
            out_file.write("$*\n")
            out_file.write("\n")
    elif platform.system() == "Windows":
        with open(str(script_file), "w") as out_file:
            out_file.write("\n")
            for arg in args:
                out_file.write("\"%s\" " % arg)
            # Pass through any script args
            out_file.write("%*\n")
            out_file.write("\n")
    else:
        raise Exception("OS ["+platform.system()+"] not supported")

# Downloads to the url to the target_file.
# Will not result in a partial file (uses a temp file).
def download_file_if_missing(url, target_file):
    if target_file.is_file():
        return
    target_file_temp = target_file.parent / (target_file.name + ".tmp")
    print("Downloading ["+str(target_file)+"]")
    print("... from ["+url+"]")
    urllib.request.urlretrieve(url, str(target_file_temp))
    target_file_temp.rename(target_file)


def rmdir(dir):
    """
    Recursively deletes the contents of a directory
    See: https://stackoverflow.com/a/49782093

    :param Path dir: The directory to delete
    """
    dir = Path(dir)
    for item in dir.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    dir.rmdir()


def yes_or_no(question):
    """
    Prompt for user input of y/n

    :param str question: The prompt to print
    """
    answer = input(question + " (y/n): ").lower().strip()
    print("")
    while not(answer == "y" or answer == "yes" or
              answer == "n" or answer == "no"):
        print("Input yes or no")
        answer = input(question + " (y/n): ").lower().strip()
        print("")
    if answer[0] == "y":
        return True
    else:
        return False


# Verify OS
if platform.system() != "Linux" and platform.system() != "Windows":
    raise Exception("OS ["+platform.system()+"] not supported")

# cac-agent version
CAC_AGENT_VERSION = 1.13
# cac-agent profiles we create (one per middleware)
CAC_AGENT_PROFILES = {
    "Linux": (
        {
            "name": "profile-safenet",
            "pkcs_library": "/usr/lib/libeTPkcs11.so"
        }, {
            "name": "profile-opensc",
            "pkcs_library": "/usr/lib/x86_64-linux-gnu/opensc-pkcs11.so"
        }, {
            "name": "profile-coolkey",
            "pkcs_library": "/usr/lib64/pkcs11/libcoolkeypk11.so"
        }
    ),
    "Windows": (
        {
            # This sets no middleware--uses Window's built-in mechanism.
            "name": "profile-default",
            "pkcs_library": None
        }, {
            "name": "profile-safenet",
            "pkcs_library": "C:\\Windows\\System32\\eTPKCS11.dll"
        }, {
            "name": "profile-opensc",
            "pkcs_library": "C:\\Program Files\\OpenSC Project\\OpenSC\\pkcs11\\opensc-pkcs11.dll"
        }
    )
}
# Profiles we used at one point, but no longer use (and actively delete)
DEPRECATED_PROFILE_DIRS = ("moesol-safenet", "moesol-opensc", "moesol-coolkey")

# The path of our python scripts
script_dir = Path(os.path.abspath(__file__)).parent
# The path of active user's home
home_dir = Path.home()
# Place to write temporary files
# NOTE: We moved this outside of the script dir so both the active user
# and the Windows Admin could reach the same dir in the event
# that the scripts are on a mounted drive (which the Admin wouldn't see).
# NOTE: This is not a secured location (other users can access).
temp_dir_insecure = Path(tempfile.gettempdir()) / \
    Path(os.path.abspath(__file__)).name
os.makedirs(str(temp_dir_insecure), mode=0o755, exist_ok=True)
# The path of the cac-agent dir within the users's home (where we're installing to)
cacagent_dir = home_dir / ".moesol/cac-agent/"
# The bin directory that includes commands in the user's PATH
bin_dir = home_dir / "bin"
# The OS hosts directory
hosts_dir = Path("c:/Windows/System32/drivers/etc")
# The new path to hosts.temp after being moved to to /etc directory
hosts_temp_file_new = hosts_dir / "hosts.temp"
# The path of the temp file we use when generating the new hosts
hosts_temp_file = temp_dir_insecure / "hosts.temp"
# The filename of a backup of the hosts file
hosts_backup_suffix = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# The OS hosts file
hosts_file = None
if platform.system() == "Linux":
    hosts_file = Path("/etc/hosts")
elif platform.system() == "Windows":
    hosts_file = Path("c:/Windows/System32/drivers/etc/hosts")

# Delete deprecated cac-agent dirs
for profile in DEPRECATED_PROFILE_DIRS:
    target_file = cacagent_dir / profile
    if target_file.exists():
        print("Deleteing deprecated ["+str(target_file)+"]")
        rmdir(target_file)

# Create cac-agent dirs
for profile in CAC_AGENT_PROFILES[platform.system()]:
    target_file = cacagent_dir / (profile["name"])
    print("Creating ["+str(target_file)+"]")
    os.makedirs(str(target_file), mode=0o700, exist_ok=True)

# Download cac-agent
download_file_if_missing(
    "https://github.com/MoebiusSolutions/cac-agent.mvn/blob/master/com/github/MoebiusSolutions/cac-jgit/%s/cac-jgit-%s-jar-with-dependencies.jar?raw=true" % (CAC_AGENT_VERSION, CAC_AGENT_VERSION),
    cacagent_dir / ("cac-jgit-%s-jar-with-dependencies.jar" % CAC_AGENT_VERSION) )
download_file_if_missing(
    "https://github.com/MoebiusSolutions/cac-agent.mvn/blob/master/com/github/MoebiusSolutions/cac-ssl-relay/%s/cac-ssl-relay-%s-jar-with-dependencies.jar?raw=true" % (CAC_AGENT_VERSION, CAC_AGENT_VERSION),
    cacagent_dir / ("cac-ssl-relay-%s-jar-with-dependencies.jar" % CAC_AGENT_VERSION) )

# Ensure bin directory exists
print("Ensuring ["+str(bin_dir)+"] exists")
os.makedirs(str(bin_dir), mode=0o700, exist_ok=True)

# Delete deprecated cac-agent scripts
for profile in DEPRECATED_PROFILE_DIRS:
    # cac-jgit
    target_file = bin_dir / ("cac-jgit."+profile)
    if target_file.exists():
        print("Deleting deprecated ["+str(target_file)+"] script")
        target_file.unlink()
    # cac-jgit...bat
    target_file = bin_dir / ("cac-jgit."+profile+".bat")
    if target_file.exists():
        print("Deleting deprecated ["+str(target_file)+"] script")
        target_file.unlink()
    # cac-ssl-relay
    target_file = bin_dir / ("cac-ssl-relay."+profile)
    if target_file.exists():
        print("Deleting deprecated ["+str(target_file)+"] script")
        target_file.unlink()
    # cac-ssl-relay...bat
    target_file = bin_dir / ("cac-ssl-relay."+profile+".bat")
    if target_file.exists():
        print("Deleting deprecated ["+str(target_file)+"] script")
        target_file.unlink()

# Create cac-agent scripts
for profile in CAC_AGENT_PROFILES[platform.system()]:
    target_file_extension = ".bat" if platform.system() == "Windows" else ""
    # cac-jgit
    target_file = bin_dir / ("cac-jgit."+profile["name"]+target_file_extension)
    print("Creating ["+str(target_file)+"] script")
    write_wrapper_script(target_file,
                         ["java", "-jar", "-Dcom.moesol.agent.profile="+profile["name"], str(cacagent_dir/("cac-jgit-%s-jar-with-dependencies.jar" % CAC_AGENT_VERSION))])
    os.chmod(str(target_file), mode=0o755)
    # cac-ssl-relay
    target_file = bin_dir / \
        ("cac-ssl-relay."+profile["name"]+target_file_extension)
    print("Creating ["+str(target_file)+"] script")
    write_wrapper_script(target_file,
                         ["java", "-jar", "-Dcom.moesol.agent.profile="+profile["name"], str(cacagent_dir/("cac-ssl-relay-%s-jar-with-dependencies.jar" % CAC_AGENT_VERSION))])
    os.chmod(str(target_file), mode=0o755)

# Install truststore.jks, pkcs11.cfg, and agent.properties
listen_port = 9090
for profile in CAC_AGENT_PROFILES[platform.system()]:
    listen_port += 1
    # truststore.jks
    file_name = "truststore.jks"
    target_file = cacagent_dir / profile["name"] / file_name
    print("Installing ["+str(target_file)+"]")
    copyfile(str(script_dir / "cac-agent" / file_name), str(target_file))
    # agent.properties
    file_name = "agent.properties"
    target_file = cacagent_dir / profile["name"] / file_name
    print("Installing ["+str(target_file)+"]")
    with open(str(script_dir / "cac-agent" / file_name), 'r') as in_file, open(str(target_file), 'w') as out_file:
        out_file.write(in_file.read().replace("9090", str(listen_port)))
    # pkcs11.cfg
    if not profile["pkcs_library"] == None:
        file_name = "pkcs11.cfg"
        target_file = cacagent_dir / profile["name"] / file_name
        print("Installing ["+str(target_file)+"]")
        with open(str(target_file), 'w') as out_file:
            out_file.write("library="+profile["pkcs_library"]+"\n")
            out_file.write("name=cac-agent\n")

# Save a backup of the hosts file
hosts_temp_backup_file = temp_dir_insecure / ("hosts_"+hosts_backup_suffix)
with open(str(hosts_file), 'r') as in_file, open(str(hosts_temp_backup_file.parent / ("hosts_"+hosts_backup_suffix)), 'w') as out_file:
    out_file.write(in_file.read())

# Remove old section from hosts file`
with open(str(hosts_file), 'r') as in_file, open(str(hosts_temp_file), 'w') as out_file:
    remove_section(in_file, out_file, '^#.*==== CAC-AGENT section start ====.*$',
                   '^#.*==== CAC-AGENT section end ====.*$')

# Generate hosts file section
hosts_file_section = ""
with open(str(script_dir / "cac-agent" / "hosts"), mode='r', newline='\n') as in_file, StringIO() as out_buffer:
    # NOTE: Ensure start/end headers are on their own line (for regex matching)
    # NOTE: We write everything using '\n' newlines, and the file writer converts to the appropriate
    # OS newlines (per the configuration specified when it was opened)
    out_buffer.write(
        "\n# ==== CAC-AGENT section start ====\n")
    out_buffer.write("# This section will be replaced by the installer\n")
    for line in in_file.readlines():
        out_buffer.write(line)
    out_buffer.write(
        "\n# ==== CAC-AGENT section end ====\n")
    hosts_file_section = out_buffer.getvalue()

# Append new section to hosts file
with open(str(hosts_temp_file), 'a') as out_file:
    out_file.write(hosts_file_section)

print("")
print("[[[ === ATTENTION === ]]]")
print("")
print("The following section must be added to your hosts file")
print("("+str(hosts_file)+").")
print("This will require admin/root access to your machine.")
print(hosts_file_section)
print("")
should_update_hosts_file = yes_or_no(
    "Should we attempt to do this automatically now?")

# Install the hosts files
if should_update_hosts_file:
    if platform.system() == "Linux":
        subprocess.run(["sudo", "install", "-o", "root", "-g", "root", "-m", "0644",
            str(hosts_temp_backup_file), str(hosts_file)+"_"+hosts_backup_suffix], check=True)
        subprocess.run(["sudo", "install", "-o", "root", "-g", "root", "-m", "0644",
            str(hosts_temp_file), str(hosts_file)], check=True)
        hosts_temp_backup_file.unlink()
        hosts_temp_file.unlink()
    elif platform.system() == "Windows":
        # Save backup of hosts to system dir
        origin = str(hosts_temp_backup_file)
        to = str(hosts_file)+"_"+hosts_backup_suffix
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe",
                                            "/c move \""+origin+"\" \""+to+"\"", None, 1)
        # Replace system hosts file
        move_command = "-executionpolicy bypass -File \"%s\" \"%s\" \"%s\" \"%s\"" % (
            # Command
            str(script_dir / "replace-file-preserving-acls.ps1"),
            # Arg: source file
            str(hosts_temp_file),
            # Arg: target file
            str(hosts_file),
            # Arg: temp file next to target (to use when assigning permissions)
            str(hosts_file)+".temp")
        print("powershell.exe "+move_command)
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", "powershell.exe", move_command, None, 1)

else:
    raise Exception("OS ["+platform.system()+"] not supported")

print("Done.")
