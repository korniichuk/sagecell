# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from os import remove, rmdir
from os.path import dirname, exists, expanduser, isdir, isfile, join
from subprocess import check_output, CalledProcessError
from sys import argv, exit

from configobj import ConfigObj

try:
    from fabric.api import local
except ImportError:
    print("Error: No module named 'fabric'. You can install it by typing:\n"
          "sudo pip install fabric")
    exit(1)

module_location = dirname(__file__)
config_sagecell_abs_path = join(module_location, "config/sagecell.ini")
config = ConfigObj(config_sagecell_abs_path)

argparse = {} # Strings for -h --help
messages = {} # Strings for output

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

    # Check Internet access
    print(messages["_ask_internet"])
    answer = raw_input()
    answer_lower = answer.lower()
    if ((answer_lower == 'n') or (answer_lower == 'no') or
            (answer_lower == 'nix')):
        print(messages["_error_Internet"])
        exit(0)
    # Update the Package Index
    local("sudo apt-get update")
    # Check git version
    try:
        git_version = check_output("git --version", shell=True)
    except CalledProcessError:
        local("echo \"Y\" | sudo apt-get install git")
        git_version = check_output("git --version", shell=True)
    git_version = git_version.replace("git version ", "").replace("\n", "")
    git_version_float = float(git_version[:3])
    if git_version_float < 1.8:
        # Update git
        local("echo \"Y\" | sudo apt-get install git")
    # Check pip
    try:
        pip_version = check_output("pip -V", shell=True)
    except CalledProcessError:
        downloads_path = expanduser("~/Downloads")
        local("cd %s; wget https://bootstrap.pypa.io/get-pip.py" %
                downloads_path)
        local("cd %s; sudo python get-pip.py" % downloads_path)
        pip_path = join(downloads_path, "get-pip.py")
        if exists(pip_path) and isfile(pip_path):
            remove(pip_path)
    # Install npm
    local("echo \"Y\" | sudo apt-get install npm")
    # Make an alias (-g -- globally)
    local("sudo ln -s /usr/bin/nodejs /usr/bin/node")
    local("sudo npm install -g inherits requirejs coffee-script")
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
    local("mv %s %s" % (join(sc_build_path, "github/sage"), sc_build_path))
    # Install Sage dependencies
    local("echo \"Y\" | sudo apt-get install gcc m4 make perl tar")
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
    # Delete empty github dir
    github_path = join(sc_build_path, "github")
    if exists(github_path) and isdir(github_path):
        rmdir(github_path)
    # Install ecdsa, lockfile, paramiko, sockjs-tornado
    local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
          "ecdsa" % sage_path)
    local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
          "lockfile" % sage_path)
    local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
          "paramiko" % sage_path)
    local("cd %s; sudo ./sage -pip install --no-deps --upgrade "
          "sockjs-tornado" % sage_path)
    # Build SageMathCell
    sagecell_path_old = join(sc_build_path, "github/sagecell")
    local("mv %s %s" % (sagecell_path_old, sage_path))
    local("cd %s; ../sage -sh -c \"make -B\"" % join(sage_path, "sagecell"))
    # Configuration
    local("cd %s; cp config_default.py config.py" % join(sage_path,
                                                         "sagecell"))
    # Check psutil
    psutil_dest_path = expanduser("~/sc_build/sage/local/lib/python2.7/psutil")
    if not exists(psutil_dest_path):
        psutil_source_path = "/usr/local/lib/python2.7/dist-packages/psutil"
        if not exists(psutil_source_path):
            # Install python-dev for psutil installation
            local("echo \"Y\" | sudo apt-get install python-dev")
            # Install psutil
            local("sudo pip install psutil")
        # Copy psutil
        local("cp %s %s" % (psutil_source_path, psutil_dest_path))
    # Check SQLAlchemy
    sqlalchemy_dest_path = expanduser("~/sc_build/sage/local/lib/python2.7/"
                                      "sqlalchemy")
    if not exists(sqlalchemy_dest_path):
        sqlalchemy_source_path = ("/usr/local/lib/python2.7/dist-packages/"
                                  "sqlalchemy")
        if not exists(sqlalchemy_source_path):
            # Install SQLAlchemy
            local("sudo pip install SQLAlchemy")
        # Copy SQLAlchemy
        local("cp %s %s" % (sqlalchemy_source_path, sqlalchemy_dest_path))

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
                        version="sagecell 0.1")
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
    """Open browser with the SageMathCell"""

    local("xdg-open http://localhost:8888")

def ssh():
    """Setup SSH for auto login to localhost without a password"""

    # Update the Package Index
    local("sudo apt-get update")
    # Install openssh-server
    local("echo \"Y\" | sudo apt-get install openssh-server")
    # Create a public and a private keys using the ssh-keygen command
    local("ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/id_rsa")
    # Copy a public key using the ssh-copy-id command
    local("ssh-copy-id localhost")
    # Ensure ssh-agent is enabled
    local("eval \"$(ssh-agent -s)\"")
    # Adds private key identities to the authentication agent
    local("ssh-add ~/.ssh/id_rsa")

def start():
    """Start the Sage Cell Server"""

    sagecell_path = expanduser("~/sc_build/sage/sagecell")
    print("Shut down the Sage Cell Server: Ctrl+c")
    local("cd %s; ../sage web_server.py" % sagecell_path)
