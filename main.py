import sys

def install_vs_build_tools():

  tmp_dir = tempfile.gettempdir()
  tmp_file = os.path.join(tmp_dir, "vs_exe")

  url = "http://go.microsoft.com/fwlink/?LinkId=691126"
  #local_filename = url.split('/')[-1]
  r = requests.get(url, stream=True)
  with open(tmp_file, 'wb') as f:
    shutil.copyfileobj(r.raw, f)

  subprocess.run(tmp_file)

try:
  import runner.vars
except ImportError:
  try:
    import Crypto #Make sure the import error was coming from trying to import the Crypto module which the lastpass package depends on
  except ImportError:
    if "--setup" in sys.argv:
      import os
      import os.path
      import subprocess
      import tempfile
      import shutil
      import platform
      from pathlib import Path
      try:
        import requests
      except ImportError:
        if os.name == "nt":
            subprocess.run("pip install requests")
        else:
            subprocess.run("pip3 install requests")
      try:
        if os.name == "nt":
            ret = subprocess.check_output("pip install pyCrypto --upgrade", shell=True)
        else:
            ret = subprocess.check_output("pip3 install pyCrypto --upgrade", shell=True)
      except subprocess.CalledProcessError:
        if os.name == "nt":
          if platform.architecture()[0] == "64bit":
              subprocess.run(Path(__file__).resolve() / "lib" / "pycrypto-2.6.1.win-amd64-py3.4.exe", shell=True)
          else:
              print("You'll need to install the 32bit pyCrypto installer from https://github.com/axper/python3-pycrypto-windows-installer")
              sys.exit()
          #If the above installer doesn't work, installing the visual studios build tools will compile visual studios when the pip command is run.
          #print("you'll need to install the visual studio build tools. A computer restart will be required")
          #install_vs_build_tools()
        else:
          raise
      import runner.vars
    else:
      raise

  try:
    import lib.drive
  except ImportError:
    if "--setup" in sys.argv:
      import subprocess
      if os.name == "nt":
          subprocess.check_output("pip install httplib2 --upgrade") #this line may not be needed
          subprocess.run("pip install --upgrade google-api-python-client")
      else:
          subprocess.check_output("pip3 install httplib2 --upgrade") #this line may not be needed
          subprocess.run("pip3 install --upgrade google-api-python-client")
      import runner.vars
    else:
      raise
  else:
    raise


if runner.vars.installed != "True":
    if "--setup" not in sys.argv:
        print("Hello matey, it looks like this is your first time running smash-utils. Let me pass you on over to the installer")
    import runner.setup
    runner.setup.main()

else:
    import runner.runner
