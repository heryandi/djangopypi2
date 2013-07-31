"""
This script does not remove existing website from nginx.
If running this script on clean Ubuntu, remember to remove the file "default" from /etc/nginx/sites-enabled/ folder.
Remember to manually run "pkill gunicorn_django" and "pkill supervisord" if need to restart the configuration steps.
"""

import errno
import os
import shutil
import subprocess

script_folder = os.path.dirname(os.path.realpath(__file__))

venv_folder = os.path.expanduser("~/venv/")
venv_conf_folder = os.path.join(venv_folder, "etc")
venv_activate_file = os.path.join(venv_folder, "bin/activate")
venv_activate_file_py = os.path.join(venv_folder, "bin/activate_this.py")

gunicorn_script = os.path.join(venv_conf_folder, "gunicorn.sh")
nginx_conf = os.path.join(venv_conf_folder, "nginx.conf")
# for soft-link
nginx_sites_available = "/etc/nginx/sites-available/djangopypi2"
nginx_sites_enabled = "/etc/nginx/sites-enabled/djangopypi2"

# list of file paths (src, dst)
copy_files = [
    (os.path.join(script_folder, "nginx.conf"), nginx_conf),
    (os.path.join(script_folder, "gunicorn.sh"), gunicorn_script),
    (os.path.join(script_folder, "supervisord.conf"), os.path.join(venv_conf_folder, "supervisord.conf"))
]

djpp_git = "https://github.com/heryandi/djangopypi2.git"
djpp_git_branch = "gsoc"
djpp_folder = os.path.join(venv_folder, "djangopypi2")
djpp_django_folder = os.path.join(djpp_folder, "djangopypi2")

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
nginx_cert = os.path.join(script_folder, "keys", "djangopypi2-cert.pem")
nginx_cert_key = os.path.join(script_folder, "keys", "djangopypi2-key.pem")
nginx_static_root = os.path.expanduser("~/.djangopypi2/")

context = dict(
    venv_folder=venv_folder,
    venv_activate_file=venv_activate_file,
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
    subprocess.call(["sudo", "apt-get", "install"] + ["nginx", "python-virtualenv"])
    subprocess.call(["virtualenv", venv_folder])
    execfile(venv_activate_file_py, dict(__file__=venv_activate_file_py))

    subprocess.call(["pip", "install", "pip", "--upgrade"])
    subprocess.call(["pip", "install", "gunicorn", "supervisor==3.0b2"])

def init_djangopypi2():
    subprocess.call(["git", "clone", djpp_git, djpp_folder])
    os.chdir(djpp_folder)
    subprocess.call(["git", "checkout", "-b", djpp_git_branch, "remotes/origin/" + djpp_git_branch])
    subprocess.call(["python", "setup.py", "develop"])
    os.chdir(djpp_django_folder)
    subprocess.call(["python", "manage_pypi_site.py", "syncdb"])
    subprocess.call(["python", "manage_pypi_site.py", "collectstatic"])
    subprocess.call(["python", "manage_pypi_site.py", "loaddata", "initial"])

def copy_config():
    make_path(venv_conf_folder)
    for src, dst in copy_files:
        fsrc = open(src)
        content = fsrc.read()
        fsrc.close()

        fdst = open(dst, "w")
        fdst.write(content.format(**context))
        fdst.close()

    # create nginx soft-links
    subprocess.call(["sudo", "ln", "-s", nginx_conf, nginx_sites_available])
    subprocess.call(["sudo", "ln", "-s", nginx_sites_available, nginx_sites_enabled])

    # make gunicorn.sh executable
    subprocess.call(["chmod", "+x", gunicorn_script])

def run_everything():
    os.chdir(venv_folder)
    execfile(venv_activate_file_py, dict(__file__=venv_activate_file_py))
    subprocess.call(["supervisord"])
    subprocess.call(["sudo", "service", "nginx", "restart"])

def make_path(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

if __name__ == "__main__":
    delete_venv_dir()
    install_prereq()
    init_djangopypi2()
    copy_config()
    run_everything()
