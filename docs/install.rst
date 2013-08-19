Installation & Configuration
============================

Installation
------------

DjangoPyPi2 is a self-contained Django project along with its apps. If you want
fine-grained control, you can looks at the sources of the apps found in the
``djangopypi2.apps`` package.

The most simple way to install ``djangopypi2`` is by::

    # Make sure we run with Bash, create a virtualenv and install packages
    $ bash
    $ virtualenv pypi-site
    $ source pypi-site/bin/activate
    $ pip install gunicorn djangopypi2

    # Configure our installation
    $ manage-pypi-site syncdb
    $ manage-pypi-site collectstatic
    $ manage-pypi-site loaddata initial

That's it, we're now ready to run our server

Where data is kept
------------------
By default ``djangopypi2`` installs and runs from ``~/.djangopypi2``, meaning
the ``.djangopypi2`` directory inside the homedir of the user running the web
server.

This can be overridden by setting the ``DJANGOPYPI2_ROOT`` environment variable.

For example, to install with a specific ``PROJECT_ROOT`` /etc/djangopypi2::
    
    # Configure our installation
    $ DJANGOPYPI2_ROOT=/etc/djangopypi2 manage-pypi-site syncdb
    $ DJANGOPYPI2_ROOT=/etc/djangopypi2 manage-pypi-site collectstatic
    $ DJANGOPYPI2_ROOT=/etc/djangopypi2 manage-pypi-site loaddata initial

Running
-------

Gunicorn
~~~~~~~~

It's easiest to see our server running by executing::

    $ gunicorn_django djangopypi2.website.settings

Then surfing to http://localhost:8000/ .

For a permanent setup, simply create a ``supervisor <http://supervisord.org/>``
configuration (you can omit the ``environment`` setting if you didn't specify a
different project root)::

    [program:djangopypi2]
    user = www-data
    directory = /path/to/virtualenv
    command = /path/to/virtualenv/bin/gunicorn_django djangopypi2.website.settings
    environment = DJANGOPYPI2_ROOT='/path/to/djangopypi2'

Apache + mod_wsgi
~~~~~~~~~~~~~~~~~

If you used ``DJANGOPYPI2_ROOT=/etc/djangopypi2`` ::

    WSGIPythonPath /usr/lib/python2.6/site-packages/djangopypi2/
    WSGIPassAuthorization On
    <VirtualHost *:80>
     
      Servername pip.example.com
      ServerAlias *.pip.example.com
    
      WSGIScriptAlias / /etc/djangopypi2/wsgi.py
    
      CustomLog logs/pip-access_log combined
      ErrorLog  logs/pip-error_log
    
    </VirtualHost>

Note : Adjust ``site-packages`` path with your python version (2.6 on centos6, 2.7 on Ubuntu as of Apr 2013)


As for /etc/djangopypi2/wsgi.py::

    import os
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
    os.environ.setdefault("DJANGOPYPI2_ROOT", "/etc/djangopypi2")
    
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()



Configuration
-------------
When first running ``djangopypi2``, a file called ``settings.json`` will be created
in the ``PROJECT_ROOT`` directory::

    {
        "DEBUG": true,
        "ADMINS": [],
        "LANGUAGE_CODE": "en-us",
        "TIME_ZONE": "America/Chicago",
        "WEB_ROOT": "/",
        "ALLOW_VERSION_OVERWRITE: "",
        "USE_HTTPS": false,

        "EMAIL_SERVER": "smtp://localhost:1025/",
        "EMAIL_USE_TLS": false,
        "EMAIL_DEFAULT_SENDER": "sender@example.com",

        "DB_ENGINE": "django.db.backends.sqlite3",
        "DB_FOLDER": "PROJECT_ROOT",
        "DB_NAME": "db.sqlite3",
        "DB_HOST": "",
        "DB_PORT": "",
        "DB_USER": "",
        "DB_PASSWORD": ""
    }

The ``DEBUG``, ``ADMINS``, ``LANGUAGE_CODE`` and ``TIME_ZONE`` are exactly the same
as in any Django ``settings.py`` file.

The ``WEB_ROOT`` setting allows for reverse proxy support. By specifying any other
root than ``/`` you can move the entire site to be served on a different web root.

The ``ALLOW_VERSION_OVERWRITE`` setting allows you to selectively allow clients to
overwrite package distributions based on the version number. This is a regular 
expression, with the default empty string meaning 'deny all'. A common use-case
example of this is to allow development versions to be overwritten, but not released
versions::

    "ALLOW_VERSION_OVERWRITE": "\\.dev.*$"

This will match ``1.0.0.dev``, ``1.0.0.dev3``, but not ``1.0.0``. Note the escaping
of the backslash character - this is required to conform to the json format. 

The ``USE_HTTPS`` setting should be set to true if ``djangopypi2`` is served over
HTTPS.

The ``EMAIL_SERVER`` should contain the SMTP server address in this format::

    smtp://username:password@host:port/

If no authentication is needed, then ``smtp://host:port/`` is sufficient.
To see the email messages sent with the default value of this setting,
run ``python -m smtpd -n -c DebuggingServer localhost:1025`` in a terminal.

The ``EMAIL_USE_TLS`` should be set to true if TLS should be used to connect to
the SMTP server.

The ``EMAIL_DEFAULT_SENDER`` setting allows you to set the default sender email
for the SMTP server.

The settings with name starting with ``DB_`` are the database settings. If you
are using sqlite3, then only these settings matter::

    "DB_ENGINE": "django.db.backends.sqlite3",
    "DB_FOLDER": "PROJECT_ROOT",
    "DB_NAME": "db.sqlite3",

``DB_FOLDER`` and ``DB_NAME`` are the directory and filename where the sqlite3
file resides respectively. For ``DB_FOLDER``, you may use the special value
``PROJECT_ROOT`` to use the value of the ``DJANGOPYPI2_ROOT`` environment
variable as the directory containing the sqlite3 file.

If you are not using sqlite3, then all settings except ``DB_FOLDER`` matters.
As an example, to setup djangopypi2 with postgreSQL::

    "DB_ENGINE": "django.db.backends.postgresql_psycopg2",
    "DB_NAME": "djangopypi2",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_USER": "postgres",
    "DB_PASSWORD": "password"

Make sure to actually create the database with name ``djangopypi2`` beforehand.
You also need to install ``psycopg2`` package separately.


Package upload directory
-------------------------
Packages are uploaded to ``PROJECT_ROOT/media/dists/`` by default.

You can change this setting by setting up a Django project with more specific
settings, or have a look at the admin interface's ``Global Configuration``
section to see if you configure your desired behavior in there.
