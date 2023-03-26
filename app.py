#!/usr/bin/python3

# IMPORTS

# Built-in modules
from os import path, remove, mkdir, makedirs # Working with files
from shutil import rmtree, move # More file stuff
from json import dump, load # Json

# External libraries
from fire import Fire # CLI tool
from requests import get # Requests
from git import Repo # Git cloning

# CONSTANTS
VERSIONS = { # Version and version keys
    "1.12.2": 2,
    "1.12": 2,

    "1.16.5": 6,
    "1.16": 6,

    "1.18.2": 8,
    "1.18": 8,

    "1.19.2": 9,
    "1.19.3": 9,
    "1.19.4": 9,
    "1.19": 9
}
SCRIPT_DIRS = ("server_scripts", "client_scripts", "startup_scripts") # Script directories
ASSET_DIRS = ("data", "assets") # Asset directories

# VARIABLES
kjspkgfile = {} # .kjspkg file

# HELPER FUNCTIONS
def _bold(s:str) -> str: return "\u001b[1m"+s+"\u001b[0m" # Make the text bold
def _err(err:str): # Handle errors
    print("\u001b[31;1m"+err+"\u001b[0m") # Print error
    exit(1) # Quit
def _create_tmp(path:str) -> str: # Create a temp directory and return its path
    makedirs("tmp/"+path, exist_ok=True)
    return "tmp/"+path

# PROJECT HELPER FUNCTIONS
def _check_project() -> bool: # Check if the current directory is a kubejs directory
    for dir in SCRIPT_DIRS:
        if path.exists(dir) and path.basename(path.abspath(path.curdir))=="kubejs": return True
    return False
def _create_project_directories(): # Create .kjspkg directories
    for dir in SCRIPT_DIRS:
        if not path.exists(dir): mkdir(dir)
        if not path.exists(dir+"/.kjspkg"): mkdir(dir+"/.kjspkg")
def _project_exists() -> bool: return path.exists(".kjspkg") # Check if a kjspkg project exists
def _delete_project(): # Delete the project and all of the files
    remove(".kjspkg")
    for dir in SCRIPT_DIRS: rmtree(dir+"/.kjspkg")
    for assetdir in SCRIPT_DIRS:
        for pkg in kjspkgfile["installed"]: rmtree(assetdir+"/"+pkg)

# PKG HELPER FUNCTIONS
def _install_pkg(pkg:str, skipmissing:bool): # Install the pkg
    if pkg in kjspkgfile["installed"]: return # If the pkg is already installed, do nothing

    package = get(f"https://github.com/Modern-Modpacks/kjspkg/raw/main/pkgs/{pkg}.json") # Get the pkg json
    if package.status_code==404: 
        if not skipmissing: _err(f"Package \"{pkg}\" does not exist") # If the json doesn't exist, err
        else: return # Or just ingore
    package = package.json() # Get the json object

    # Unsupported version/modloader errs
    if kjspkgfile["version"] not in package["versions"]: _err(f"Unsupported version 1.{10+kjspkgfile['version']} for package \"{pkg}\"")
    if kjspkgfile["modloader"] not in package["modloaders"]: _err(f"Unsupported modloader \"{kjspkgfile['modloader'].title()}\" for package \"{pkg}\"")

    tmpdir = _create_tmp(pkg) # Create a temp dir
    Repo.clone_from(f"https://github.com/{package['repo']}.git", tmpdir) # Install the repo into the tmp dir
    for dir in SCRIPT_DIRS+ASSET_DIRS: # Clone assets and scripts into the main kjs folders
        tmppkgpath = tmpdir+"/"+dir
        pkgpath = dir+"/.kjspkg/"+pkg if dir in SCRIPT_DIRS else dir+"/"+pkg
        if path.exists(tmppkgpath): move(tmppkgpath, pkgpath)

    kjspkgfile["installed"].append(pkg) # Add the pkg name to .kjspkg
def _remove_pkg(pkg:str, skipmissing:bool): # Remove the pkg
    if pkg not in kjspkgfile["installed"]:
        if not skipmissing: _err(f"Package \"{pkg}\" is not installed") # If the pkg is not installed, err
        else: return # Or just ignore

    for dir in SCRIPT_DIRS+ASSET_DIRS: # Remove all associated files
        pkgpath = dir+"/.kjspkg/"+pkg if dir in SCRIPT_DIRS else dir+"/"+pkg
        if path.exists(pkgpath): rmtree(pkgpath)

    kjspkgfile["installed"].remove(pkg) # Remove the pkg name from .kjspkg

# COMMAND FUNCTIONS
def install(*pkgs:str, quiet:bool=False, skipmissing:bool=False): # Install pkgs
    for pkg in pkgs:
        pkg = pkg.lower()
        _install_pkg(pkg, skipmissing)
        if not quiet: print(_bold(f"Package \"${pkg}\" installed succesfully!"))
def removepkg(*pkgs:str, quiet:bool=False, skipmissing:bool=False): # Remove pkgs
    for pkg in pkgs:
        pkg = pkg.lower()
        _remove_pkg(pkg, skipmissing)
        if not quiet: print(_bold(f"Package \"${pkg}\" removed succesfully!"))
def listmods(*, count:bool=False): # List pkgs
    if count: # Only show the pkg count if the "count" option is passed
        print(len(kjspkgfile["installed"]))
        return

    print("\n".join(kjspkgfile["installed"]))
def init(*, version:str=None, modloader:str=None, quiet:bool=False, override:bool=False): # Init project
    global kjspkgfile

    if not _check_project(): _err("Hmm... This directory doesn't look like a kubejs directory") # Wrong dir err

    if _project_exists(): # Override
        if not quiet and input("\u001b[31;1mA PROJECT ALREADY EXISTS IN THIS REPOSITORY, CREATING A NEW ONE OVERRIDES THE PREVIOUS ONE, ARE YOU SURE YOU WANT TO PROCEED? (y/N): \u001b[0m").lower()=="y" or override: _delete_project()
        else: exit(0)

    # Ask for missing params
    if not version: version = input(_bold("Input your minecraft version (1.12/1.16/1.18/1.19): "))
    if version not in VERSIONS.keys(): _err("Unknown or unsupported version: "+version)

    if not modloader: modloader = input(_bold("Input your modloader (forge/fabric/quilt): "))
    modloader = modloader.lower()
    if modloader not in ("forge", "fabric", "quilt"): _err("Unknown or unsupported modloader: "+modloader.title())

    _create_project_directories() # Create .kjgpkg directories
    kjspkgfile = {
        "version": VERSIONS[version],
        "modloader": modloader if modloader!="quilt" else "fabric",
        "installed": []
    }
    with open(".kjspkg", "w+") as f: dump(kjspkgfile, f) # Create .kjspkg file
    if not quiet: print(_bold("Project created!")) # Woo!
def uninit(*, confirm:bool=False): # Remove the project
    if confirm or input("\u001b[31;1mDOING THIS WILL REMOVE ALL PACKAGES AND UNINSTALL KJSPKG COMPLETELY, ARE YOU SURE YOU WANT TO PROCEED? (y/N): \u001b[0m").lower()=="y": _delete_project() 
def info(): # Print the help page
    INFO = f"""
{_bold("Commands:")}

kjspkg install [pkgname1] [pkgname2] [--quiet/--skipmissing] - installs packages
kjspkg remove/uninstall [pkgname1] [pkgname2] [--quiet/--skipmissing] - removes packages
kjspkg list [--count] - lists packages (or outputs the count of them)

kjspkg init [--override/--quiet] [--version "<version>"] [--modloader "<modloader>"] - inits a new project (will be run by default)
kjspkg uninit [--confirm] - removes all packages and the project

kjspkg help/info - shows this message

{_bold("Contributors:")}

Modern Modpacks - owner
G_cat101 - coder
    """

    print(INFO)
    
# PARSER FUNCTION
def _parser(func:str="help", *args, help:bool=False, **kwargs):
    global kjspkgfile

    if help: func="help"

    FUNCTIONS = { # Command mappings
        "install": install,
        "remove": removepkg,
        "uninstall": removepkg,
        "list": listmods,
        "init": init,
        "uninit": uninit,
        "help": info,
        "info": info
    }

    if func not in FUNCTIONS.keys(): _err("Command \""+func+"\" is not found. Run \"kjspkg help\" to see all of the available commands") # Wrong command err

    if func not in ("init", "help") and not _project_exists(): # If a project is not found, call init
        print(_bold("Project not found, a new one will be created.\n"))
        init()

    if path.exists(".kjspkg"): kjspkgfile = load(open(".kjspkg")) # Open .kjspkg

    FUNCTIONS[func](*args, **kwargs) # Run the command

    # Clean up
    if path.exists(".kjspkg"): # If uninit wasn't called
        with open(".kjspkg", "w") as f: dump(kjspkgfile, f) # Save .kjspkg
    if path.exists("tmp"): rmtree("tmp") # Remove tmp

# RUN
if __name__=="__main__": # If not imported
    try: Fire(_parser) # Run parser with fire
    except (KeyboardInterrupt, EOFError): exit(0) # Ignore some exceptions

# Ok that's it bye