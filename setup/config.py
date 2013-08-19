"""
This script does not remove existing website from nginx.
If running this script on clean Ubuntu, remember to remove the file "default" from /etc/nginx/sites-enabled/ folder.
Remember to manually run "pkill gunicorn_django" and "pkill supervisord" if need to restart the configuration steps.
"""

import errno
import os
import shutil
import subprocess

from conf.github_oauth import *

root_folder = os.path.dirname(os.path.realpath(__file__))
conf_folder = os.path.join(root_folder, "conf")
keys_folder = os.path.join(root_folder, "keys")
requirements_file = os.path.join(conf_folder, "requirements.txt")

venv_folder = os.path.expanduser("~/venv/")
#venv_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test")
venv_conf_folder = os.path.join(venv_folder, "etc")
#venv_conf_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test")
venv_activate_file = os.path.join(venv_folder, "bin/activate")
venv_activate_file_py = os.path.join(venv_folder, "bin/activate_this.py")

djpp_git = "https://github.com/heryandi/djangopypi2.git"
djpp_git_branch = "gsoc"
djpp_folder = os.path.join(venv_folder, "djangopypi2")
djpp_django_folder = os.path.join(djpp_folder, "djangopypi2")

gunicorn_script = os.path.join(venv_conf_folder, "gunicorn.sh")
nginx_conf = os.path.join(venv_conf_folder, "nginx.conf")
# list of file paths to copy (src, dst)
copy_files = [
    (os.path.join(conf_folder, "nginx.conf"), nginx_conf),
    (os.path.join(conf_folder, "gunicorn.sh"), gunicorn_script),
    (os.path.join(conf_folder, "supervisord.conf"), os.path.join(venv_conf_folder, "supervisord.conf")),
    (os.path.join(conf_folder, "initial.json"), os.path.join(djpp_django_folder, "website", "fixtures", "initial.json")),
    (os.path.join(conf_folder, "settings.json"), os.path.expanduser("~/.djangopypi2/")),
]

# for soft-link
nginx_sites_available = "/etc/nginx/sites-available/djangopypi2"
nginx_sites_enabled = "/etc/nginx/sites-enabled/djangopypi2"

"""
Variables used to generate configuration files
"""
djpp_data_github_client_name = GITHUB_CLIENT_NAME
djpp_data_github_client_id = GITHUB_APP_ID
djpp_data_github_client_secret = GITHUB_APP_SECRET

djpp_email_default_sender = "sender@example.org"
djpp_email_use_tls = "false"
djpp_email_server = "smtp://localhost:1025/"

djpp_db_name = "djangopypi2"
djpp_db_host = "localhost"
djpp_db_port = "5432"
djpp_db_user = "postgres"
djpp_db_password = "password"

gunicorn_worker = 3
gunicorn_user = "user"
gunicorn_group = "user"
gunicorn_logfile = os.path.expanduser("~/.djangopypi2/gunicorn.log")
gunicorn_djpp_folder = djpp_django_folder

supervisor_user = "user"
supervisor_directory = djpp_django_folder
supervisor_command = os.path.join(venv_conf_folder, "gunicorn.sh")
supervisor_djpp_log = os.path.join(venv_conf_folder, "supervisord_djangopypi2.log")
supervisor_log = "/tmp/supervisord.log"

nginx_server_name = "localhost"
nginx_local_website = "http://localhost:8000"
nginx_root = djpp_django_folder
nginx_log = "/tmp/nginx.log"
nginx_cert = os.path.join(keys_folder, "djangopypi2-cert.pem")
nginx_cert_key = os.path.join(keys_folder, "djangopypi2-key.pem")
nginx_static_root = os.path.expanduser("~/.djangopypi2/")

context = dict(
    venv_folder=venv_folder,
    venv_activate_file=venv_activate_file,

    client_name=djpp_data_github_client_name,
    client_id=djpp_data_github_client_id,
    client_secret=djpp_data_github_client_secret,

    email_default_sender = djpp_email_default_sender,
    email_use_tls = djpp_email_use_tls,
    email_server = djpp_email_server,

    db_name = djpp_db_name,
    db_host = djpp_db_host,
    db_port = djpp_db_port,
    db_user = djpp_db_user,
    db_password = djpp_db_password,

    gunicorn_worker=gunicorn_worker,
    gunicorn_user=gunicorn_user,
    gunicorn_group=gunicorn_group,
    gunicorn_logfile=gunicorn_logfile,
    gunicorn_djpp_folder=gunicorn_djpp_folder,

    supervisor_user=supervisor_user,
    supervisor_directory=supervisor_directory,
    supervisor_command=supervisor_command,
    supervisor_djpp_log=supervisor_djpp_log,
    supervisor_log=supervisor_log,

    nginx_server_name=nginx_server_name,
    nginx_local_website=nginx_local_website,
    nginx_root=nginx_root,
    nginx_log=nginx_log,
    nginx_cert=nginx_cert,
    nginx_cert_key=nginx_cert_key,
    nginx_static_root=nginx_static_root
)

def delete_venv_dir():
    if os.path.isdir(venv_folder):
        shutil.rmtree(venv_folder)

def install_prereq():
    subprocess.call(["sudo", "apt-get", "update"])
    subprocess.call(["sudo", "apt-get", "-y", "install"] + ["nginx", "python-virtualenv", "postgresql", "libpq-dev"])
    subprocess.call(["virtualenv", venv_folder])
    execfile(venv_activate_file_py, dict(__file__=venv_activate_file_py))

    subprocess.call(["pip", "install", "pip", "--upgrade"])
    subprocess.call(["pip", "install", "-r", requirements_file])

def clone_djangopypi2():
    subprocess.call(["git", "clone", djpp_git, djpp_folder])
    os.chdir(djpp_folder)
    subprocess.call(["git", "checkout", "-b", djpp_git_branch, "remotes/origin/" + djpp_git_branch])
    subprocess.call(["python", "setup.py", "develop"])

def copy_config():
    for src, dst in copy_files:
        make_path(os.path.dirname(dst))
        fsrc = open(src)
        content = fsrc.read()
        fsrc.close()

        fdst = open(dst, "w")
        fdst.write(content.format(**context))
        fdst.close()

    # make gunicorn.sh executable
    subprocess.call(["chmod", "+x", gunicorn_script])

def create_softlink():
    subprocess.call(["sudo", "ln", "-s", nginx_conf, nginx_sites_available])
    subprocess.call(["sudo", "ln", "-s", nginx_sites_available, nginx_sites_enabled])

def init_djangopypi2():
    os.chdir(djpp_django_folder)
    subprocess.call(["python", "manage_pypi_site.py", "syncdb"])
    subprocess.call(["python", "manage_pypi_site.py", "collectstatic"])
    subprocess.call(["python", "manage_pypi_site.py", "loaddata", "initial"])

def run_everything():
    os.chdir(venv_folder)
    execfile(venv_activate_file_py, dict(__file__=venv_activate_file_py))
    subprocess.call(["supervisord"])
    subprocess.call(["sudo", "service", "nginx", "restart"])

def make_path(path):
    if os.path.isdir(path):
        return
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

if __name__ == "__main__":
    delete_venv_dir()
    install_prereq()
    clone_djangopypi2()
    copy_config()
    create_softlink()
    init_djangopypi2()
    run_everything()
