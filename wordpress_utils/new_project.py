''' creates and setups a new _s theme and uploads it to webfaction. '''


import subprocess, os.path

import paramiko
from runner import vars

def assert_webfaction_dir_exists(the_dir):

    res = vars.webfaction.system(vars.wf_id, "test -d " + the_dir + " && echo Exists!!")
    if res.strip():
        raise Exception('Whoa, we don\'t want to be overwriting code. The following theme already exists on the webfaction server: ' + the_dir)
    return res


    # transport = paramiko.Transport(vars.ftp_host)
    # transport.connect(username=vars.ftp_username, password=vars.ftp_password)
    # sftp=paramiko.SFTPClient.from_transport(transport)
    # try:
    #     filestat = sftp.stat(vars.webfaction_theme_dir)
    # except IOError:
    #     pass
    # else:
    #     raise Exception('Whoa, we don\'t want to be overwriting code. The following theme already exists on the webfaction server: ' + the_dir)
assert_webfaction_dir_exists(vars.webfaction_theme_dir)

subprocess.call('git clone https://github.com/sebodev/_s %s' % vars.project_dir, shell=True)

print('\n_s Download complete\nuploading _s to webfaction...')
command = r'pscp -scp -i %UserProfile%\.ssh\sitesmash.ppk -r {} sebodev@webfaction:{}'.format(vars.project_dir, vars.webfaction_theme_dir)
subprocess.call(command, cwd=vars.project_dir, shell=True)
#session=ssh.SSHSession(vars.ftp_host, vars.ftp_username, vars.ftp_password)
#session.put_all(project_dir, vars.webfaction_theme_dir)


print('Upload complete. Configuring project...')
from . import configure_project
configure_project.setup("sebodev")
