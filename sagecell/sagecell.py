# -*- coding: utf-8 -*-

from argparse import ArgumentParser
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
    """Install the Sage Cell Server"""

    # Check distro:
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
        pip_version = check_output("pip -V", shell=True)
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
    # Download repositories from GitHub/
    # Create a directory for building images
    sc_build_path = expanduser("~/sc_build")
    local("mkdir %s" % sc_build_path)
    # Get clone_repositories
    local("cd %s; wget https://github.com/sagemath/sagecell"
          "/raw/master/contrib/vm/clone_repositories" % sc_build_path)
    # Make clone_repositories bash script executable
    local("cd %s; chmod u+x clone_repositories" % sc_build_path)
    # Run clone_repositories bash script
    local("cd %s; ./clone_repositories" % sc_build_path)
    # /Download repositories from GitHub
    # Move sage folder
    sage_path_old = join(sc_build_path, "github/sage")
    local("mv %s %s" % (sage_path_old, sc_build_path))
    # Install Sage dependencies
    if distro == "ubuntu":
        local("echo \"Y\" | sudo apt-get install gcc m4 make perl tar")
    elif distro == "debian":
        local("su -c \"echo \"Y\" | apt-get install gcc m4 make perl tar\"")
    # Build Sage
    sage_path = join(sc_build_path, "sage")
    local("cd %s; make start" % sage_path)
    # We need IPython stuff, not present in spkg
    local("cd %s; rm -rf IPython*" % join(sage_path,
            "local/lib/python/site-packages"))
    local("cd %s; rm -rf ipython*" % join(sage_path,
            "local/lib/python/site-packages"))
    ipython_path = join(sc_build_path, "github/ipython")
    local("mv %s %s" % (ipython_path, sage_path))
    local("cd %s; ../sage setup.py develop" % join(sage_path, "ipython"))
    # We need a cutting-edge matplotlib
    matplotlib_path = join(sc_build_path, "github/matplotlib")
    local("mv %s %s" % (matplotlib_path, sage_path))
    local("cd %s; ../sage setup.py install" % join(sage_path, "matplotlib"))
    # Install ecdsa, lockfile, paramiko, sockjs-tornado
    if distro == "ubuntu":
        local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
              "ecdsa" % sage_path)
        local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
              "lockfile" % sage_path)
        local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
              "paramiko" % sage_path)
        local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
              "sockjs-tornado" % sage_path)
    elif distro == "debian":
        local("cd %s; su -c \"echo \"Y\" | ./sage -pip install "
              "--no-deps --upgrade ecdsa\"" % sage_path)
        local("cd %s; su -c \"echo \"Y\" | ./sage -pip install "
              "--no-deps --upgrade lockfile\"" % sage_path)
        local("cd %s; su -c \"echo \"Y\" | ./sage -pip install "
              "--no-deps --upgrade paramiko\"" % sage_path)
        local("cd %s; su -c \"echo \"Y\" | ./sage -pip install "
              "--no-deps --upgrade sockjs-tornado\"" % sage_path)
    # Move sagecell folder
    sagecell_path_old = join(sc_build_path, "github/sagecell")
    local("mv %s %s" % (sagecell_path_old, sage_path))
    # Delete empty github dir
    github_path = join(sc_build_path, "github")
    if exists(github_path) and isdir(github_path):
        rmdir(github_path)
    # Build SageMathCell
    local("cd %s; ../sage -sh -c \"make -B\"" % join(sage_path, "sagecell"))
    # Configuration
    local("cd %s; cp config_default.py config.py" % join(sage_path,
                                                         "sagecell"))
    # Check psutil
    psutil_path = expanduser("~/sc_build/sage/local/lib/python2.7/psutil")
    if not exists(psutil_path):
        # Install python-dev for psutil installation
        if distro == "ubuntu":
            local("echo \"Y\" | sudo apt-get install python-dev")
        elif distro == "debian":
            local("su -c \"echo \"Y\" | apt-get install python-dev\"")
        # Install psutil
        if distro == "ubuntu":
            local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
                  "psutil" % sage_path)
        elif distro == "debian":
            local("cd %s; su -c \"echo \"Y\" | ./sage -pip install "
                  "--no-deps --upgrade psutil\"" % sage_path)
    # Check SQLAlchemy
    sqlalchemy_path = expanduser("~/sc_build/sage/local/lib/python2.7/"
                                 "sqlalchemy")
    if not exists(sqlalchemy_path):
        # Install SQLAlchemy
        if distro == "ubuntu":
            local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
                  "SQLAlchemy" % sage_path)
        elif distro == "debian":
            local("cd %s; su -c \"echo \"Y\" | ./sage -pip install "
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
                        version="sagecell 0.2a2")
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
    if len(argv) == 1:
        parser.print_help()
        exit(0) # Clean exit without any errors/problems
    return parser.parse_args()

def open_sagemathcell():
    """Open browser with the Sage Cell Server"""

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
    """Start the Sage Cell Server"""

    sagecell_path = expanduser("~/sc_build/sage/sagecell")
    local("cd %s; ../sage web_server.py" % sagecell_path)
