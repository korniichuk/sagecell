# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from errno import EACCES
from os import remove, rmdir
from os.path import dirname, exists, expanduser, isdir, isfile, join
from platform import platform
from subprocess import check_output, CalledProcessError
from sys import argv, exit

from configobj import ConfigObj

try:
    from fabric.api import local
except ImportError:
    print("Error: No module named 'fabric'. You can install it by typing:\n"
          "    sudo pip install fabric\nor\n    su -c \"pip install fabric\"")
    exit(1)

module_location = dirname(__file__)
config_sagecell_abs_path = join(module_location, "config/sagecell.ini")
config = ConfigObj(config_sagecell_abs_path)

argparse = {} # Strings for -h --help
messages = {} # Strings for output

def auto():
    """Start the SageMathCell automatically on boot"""

    # Check distro
    distro = check_distro()
    if distro == None:
        print(messages["_unsupported_distro"])
        print(messages["_ask_distro"].format("\n"))
        answer = raw_input()
        answer_lower = answer.lower()
        if (answer_lower == '0') or (answer_lower == 'o'):
            exit(0)
        elif answer_lower == '1':
            distro = "ubuntu"
        elif answer_lower == '2':
            distro = "debian"
        else:
            print(messages["_error_UnknownValue"])
            exit(0)
    # Update the Package Index
    if distro == "ubuntu":
        local("sudo apt-get update")
    elif distro == "debian":
        local("su -c \"apt-get update\"")
    # Install screen
    if distro == "ubuntu":
        local("echo \"Y\" | sudo apt-get install screen")
    elif distro == "debian":
        local("su -c \"echo \"Y\" | apt-get install screen\"")
    # rc.local
    rc_local_abs_path = "/etc/rc.local"
    if exists(rc_local_abs_path) and isfile(rc_local_abs_path):
        try:
            with open(rc_local_abs_path, 'r') as f:
                rc_local_lines = f.readlines()
        except Exception as exception: # Python3 PermissionError
            error_code = exception.errno
            if error_code == EACCES: # 13
                print(messages["_error_NoRoot"])
                exit(1)
            else:
                print(messages["_error_Oops"] % strerror(error_code))
                exit(1)
    else:
        # Create /etc/rc.local file
        rc_local_lines = ["#!/bin/sh -e\n", "\n", "# rc.local\n", "\n",
                          "exit 0\n"]
        try:
            with open(rc_local_abs_path, 'w') as f:
                for line in rc_local_lines:
                    f.write(line)
        except Exception as exception: # Python3 PermissionError
            error_code = exception.errno
            if error_code == EACCES: # 13
                print(messages["_error_NoRoot"])
                exit(1)
            else:
                print(messages["_error_Oops"] % strerror(error_code))
                exit(1)
        # Make rc.local file executable
        local("chmod u+x %s" % rc_local_abs_path)
    try:
        with open(rc_local_abs_path, 'w') as f:
            for line in rc_local_lines:
                line_strip = line.strip()
                if line_strip == "exit 0":
                    print(messages["_ask_username"].format("\n"))
                    answer = raw_input()
                    answer_lower = answer.lower()
                    username = answer_lower
                    if distro == "ubuntu":
                        f.write("sudo -u %s screen -dmS sagecell "
                                "/usr/local/bin/sagecellscript\n\n" %
                                username)
                    elif distro == "debian":
                        f.write("su %s -c \"screen -dmS sagecell "
                                "/usr/local/bin/sagecellscript\"\n\n" %
                                username)
                f.write(line)
    except Exception as exception: # Python3 PermissionError
        error_code = exception.errno
        if error_code == EACCES: # 13
            print(messages["_error_NoRoot"])
            exit(1)
        else:
            print(messages["_error_Oops"] % strerror(error_code))
            exit(1)

def check_distro():
    """Check linux distro"""

    distro = None

    platform_str = platform()
    platform_str_lower = platform_str.lower()
    if "ubuntu" in platform_str_lower:
        distro = "ubuntu"
    elif "debian" in platform_str_lower:
        distro = "debian"
    return distro

def create_dictionaries():
    """Create "argparse" and "messages" dictionaries"""

    config_argparse_rel_path = config["config_argparse_rel_path"]
    config_argparse_abs_path = join(module_location, config_argparse_rel_path)
    config_messages_rel_path = config["config_messages_rel_path"]
    config_messages_abs_path = join(module_location, config_messages_rel_path)
    with open(config_argparse_abs_path, 'r') as f:
        argparse_list = f.read().splitlines()
    for i in range(0, len(argparse_list), 2):
        argparse[argparse_list[i]] = argparse_list[i+1]
    with open(config_messages_abs_path, 'r') as f:
        messages_list = f.read().splitlines()
    for i in range(0, len(messages_list), 2):
        messages[messages_list[i]] = messages_list[i+1]

def install():
    """Install the SageMathCell"""

    # Check distro
    distro = check_distro()
    if distro == None:
        print(messages["_unsupported_distro"])
        print(messages["_ask_distro"].format("\n"))
        answer = raw_input()
        answer_lower = answer.lower()
        if (answer_lower == '0') or (answer_lower == 'o'):
            exit(0)
        elif answer_lower == '1':
            distro = "ubuntu"
        elif answer_lower == '2':
            distro = "debian"
        else:
            print(messages["_error_UnknownValue"])
            exit(0)
    # Check Internet access
    print(messages["_ask_internet"])
    answer = raw_input()
    answer_lower = answer.lower()
    if ((answer_lower == 'n') or (answer_lower == 'no') or
            (answer_lower == 'nix')):
        print(messages["_error_Internet"])
        exit(0)
    # Update the Package Index
    if distro == "ubuntu":
        local("sudo apt-get update")
    elif distro == "debian":
        local("su -c \"apt-get update\"")
    # Check git version
    try:
        git_version = check_output("git --version", shell=True)
    except CalledProcessError:
        # Install git
        if distro == "ubuntu":
            local("echo \"Y\" | sudo apt-get install git")
        elif distro == "debian":
            local("su -c \"echo \"Y\" | apt-get install git\"")
        git_version = check_output("git --version", shell=True)
    git_version = git_version.replace("git version ", "").replace("\n", "")
    git_version_float = float(git_version[:3])
    if git_version_float < 1.8:
        # Update git
        if distro == "ubuntu":
            local("echo \"Y\" | sudo apt-get install git")
        elif distro == "debian":
            local("su -c \"echo \"Y\" | apt-get install git\"")
    # Check pip
    try:
        pip_version = check_output("pip --version", shell=True)
    except CalledProcessError:
        # Install pip
        if distro == "ubuntu":
            downloads_path = expanduser("~/Downloads")
            local("cd %s; wget https://bootstrap.pypa.io/get-pip.py" %
                    downloads_path)
            local("cd %s; sudo python get-pip.py" % downloads_path)
            pip_path = join(downloads_path, "get-pip.py")
            if exists(pip_path) and isfile(pip_path):
                remove(pip_path)
        elif distro == "debian":
            # Install python-dev for pip installation
            local("su -c \"echo \"Y\" | apt-get install python-dev\"")
            local("su -c \"echo \"Y\" | apt-get install python-pip\"")
    # Install npm
    if distro == "ubuntu":
        local("echo \"Y\" | sudo apt-get install npm")
    elif distro == "debian":
        # Install curl for node.js, npm installations
        local("su -c \"echo \"Y\" | apt-get install curl\"")
        # Install node.js for npm installation
        local("su -c \"curl --silent --location "
              "https://deb.nodesource.com/setup_0.12 | bash -\"")
        local("su -c \"echo \"Y\" | apt-get install --yes nodejs\"")
        local("su -c \"curl https://www.npmjs.com/install.sh | sh\"")
    # Make an alias
    nodejs_alias_abs_path = "/usr/bin/node"
    if not exists(nodejs_alias_abs_path):
        if distro == "ubuntu":
            local("sudo ln -s /usr/bin/nodejs %s" % nodejs_alias_abs_path)
        elif distro == "debian":
            local("su -c \"ln -s /usr/bin/nodejs %s\"" % nodejs_alias_abs_path)
    # Install js: inherits, requirejs, coffee-script (-g -- globally)
    if distro == "ubuntu":
        local("sudo npm install -g inherits requirejs coffee-script")
    elif distro == "debian":
        local("su -c \"npm install -g inherits requirejs coffee-script\"")
    # Create a directory for all components
    sc_build_path = expanduser("~/sc_build")
    local("mkdir %s" % sc_build_path)
    # Get Sage
    local("cd %s; git clone https://github.com/novoselt/sage.git" %
            sc_build_path)
    sage_path = join(sc_build_path, "sage")
    local("cd %s; git checkout sagecell" % sage_path)
    local("cd %s; git submodule update --init --recursive" % sage_path)
    # Install Sage dependencies
    if distro == "ubuntu":
        local("echo \"Y\" | sudo apt-get install gcc m4 make perl tar")
    elif distro == "debian":
        local("su -c \"echo \"Y\" | apt-get install gcc m4 make perl tar\"")
    # Build Sage
    local("cd %s; make" % sage_path)
    # Install threejs
    if distro == "ubuntu":
        local("cd %s; sudo ./sage -i threejs" % sage_path)
    elif distro == "debian":
        local("cd %s; su -c \"./sage -i threejs\"" % sage_path)
    # We need IPython stuff, not present in spkg
    local("cd %s; rm -rf IPython*" % join(sc_build_path,
            "sage/local/lib/python/site-packages"))
    local("cd %s; rm -rf ipython*" % join(sc_build_path,
            "sage/local/lib/python/site-packages"))
    local("cd %s; git clone https://github.com/novoselt/ipython.git" %
            sc_build_path)
    local("cd %s; git checkout sagecell" % join(sc_build_path, "ipython"))
    local("cd %s; git submodule update --init --recursive" %
            join(sc_build_path, "ipython"))
    local("cd %s; ../sage/sage setup.py develop" % join(sc_build_path,
                                                        "ipython"))
    # Install python-dev for psutil installation
    if distro == "ubuntu":
        local("echo \"Y\" | sudo apt-get install python-dev")
    elif distro == "debian":
        local("su -c \"echo \"Y\" | apt-get install python-dev\"")
    # Install ecdsa, lockfile, paramiko, psutil, sockjs-tornado
    if distro == "ubuntu":
        local("cd %s; sudo sage/sage -pip install --no-deps --upgrade "
              "ecdsa" % sc_build_path)
        local("cd %s; sudo sage/sage -pip install --no-deps --upgrade "
              "lockfile" % sc_build_path)
        local("cd %s; sudo sage/sage -pip install --no-deps --upgrade "
              "paramiko" % sc_build_path)
        local("cd %s; sudo sage/sage -pip install --no-deps --upgrade "
              "psutil" % sc_build_path)
        local("cd %s; sudo sage/sage -pip install --no-deps --upgrade "
              "sockjs-tornado" % sc_build_path)
    elif distro == "debian":
        local("cd %s; su -c \"sage/sage -pip install "
              "--no-deps --upgrade ecdsa\"" % sc_build_path)
        local("cd %s; su -c \"sage/sage -pip install "
              "--no-deps --upgrade lockfile\"" % sc_build_path)
        local("cd %s; su -c \"sage/sage -pip install "
              "--no-deps --upgrade paramiko\"" % sc_build_path)
        local("cd %s; su -c \"sage/sage -pip install "
              "--no-deps --upgrade psutil\"" % sc_build_path)
        local("cd %s; su -c \"sage/sage -pip install "
              "--no-deps --upgrade sockjs-tornado\"" % sc_build_path)
    # Build SageMathCell
    local("cd %s; git clone https://github.com/sagemath/sagecell.git" %
            sc_build_path)
    local("cd %s; git submodule update --init --recursive" %
            join(sc_build_path, "sagecell"))
    local("cd %s; ../sage/sage -sh -c \"make -B\"" % join(sc_build_path,
                                                          "sagecell"))
    # Configuration
    local("cd %s; cp config_default.py config.py" % join(sc_build_path,
                                                         "sagecell"))
    # Check SQLAlchemy
    sqlalchemy_path = expanduser("~/sc_build/sage/sage/local/lib/python2.7/"
                                 "sqlalchemy")
    if not exists(sqlalchemy_path):
        # Install SQLAlchemy
        if distro == "ubuntu":
            local("cd %s; sudo sage/sage -pip install --no-deps --upgrade "
                  "SQLAlchemy" % sage_path)
        elif distro == "debian":
            local("cd %s; su -c \"sage/sage -pip install "
                  "--no-deps --upgrade SQLAlchemy\"" % sage_path)
    print(messages["_installed"])

def main():
    """Main function"""

    create_dictionaries()
    args = parse_command_line_args()
    args.function_name()

def parse_command_line_args():
    """Parse command line arguments"""

    # Create top parser
    parser = ArgumentParser(prog="sagecell", description=argparse["_parser"],
                            add_help=True)
    parser.add_argument("-v", "--version", action="version",
                        version="sagecell 0.3a1")
    # Create subparsers for the top parser
    subparsers = parser.add_subparsers(title=argparse["_subparsers"])
    # Create the parser for the "install" subcommand
    parser_install = subparsers.add_parser("install",
            description=argparse["_parser_install"],
            help=argparse["_parser_install"])
    parser_install.set_defaults(function_name=install)
    # Create the parser for the "start" subcommand
    parser_list = subparsers.add_parser("start",
            description=argparse["_parser_start"],
            help=argparse["_parser_start"])
    parser_list.set_defaults(function_name=start)
    # Create the parser for the "open" subcommand
    parser_list = subparsers.add_parser("open",
            description=argparse["_parser_open"],
            help=argparse["_parser_open"])
    parser_list.set_defaults(function_name=open_sagemathcell)
    # Create the parser for the "ssh" subcommand
    parser_list = subparsers.add_parser("ssh",
            description=argparse["_parser_ssh"],
            help=argparse["_parser_ssh"])
    parser_list.set_defaults(function_name=ssh)
    # Create the parser for the "auto" subcommand
    parser_list = subparsers.add_parser("auto",
            description=argparse["_parser_auto"],
            help=argparse["_parser_auto"])
    parser_list.set_defaults(function_name=auto)
    if len(argv) == 1:
        parser.print_help()
        exit(0) # Clean exit without any errors/problems
    return parser.parse_args()

def open_sagemathcell():
    """Open browser with the SageMathCell"""

    local("xdg-open http://localhost:8888")

def ssh():
    """Setup SSH for auto login to localhost without a password"""

    # Update the Package Index
    try:
        # Ubuntu linux distro
        local("sudo apt-get update")
    except:
        # Debian linux distro
        local("su -c \"apt-get update\"")
    # Install openssh-server
    try:
        # Ubuntu linux distro
        local("echo \"Y\" | sudo apt-get install openssh-server")
    except:
        # Debian linux distro
        local("su -c \"echo \"Y\" | apt-get install openssh-server\"")
    # Create a public and a private keys using the ssh-keygen command
    local("ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/id_rsa")
    # Copy a public key using the ssh-copy-id command
    local("ssh-copy-id localhost")
    # Ensure ssh-agent is enabled and adds private key identities
    # to the authentication agent
    local("eval \"$(ssh-agent -s)\"; ssh-add ~/.ssh/id_rsa")

def start():
    """Start the SageMathCell"""

    sagecell_path = expanduser("~/sc_build/sage/sagecell")
    local("cd %s; ../sage/sage web_server.py" % sagecell_path)
