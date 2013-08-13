#!/bin/bash
set -e
LOGFILE={gunicorn_logfile}
LOGDIR=$(dirname $LOGFILE)
test -d $LOGDIR || mkdir -p $LOGDIR

NUM_WORKERS={gunicorn_worker}
USER={gunicorn_user}
GROUP={gunicorn_group}

source {venv_activate_file}
cd {gunicorn_djpp_folder}

# Finally, the invocation
gunicorn_django -w $NUM_WORKERS --user=$USER --group=$GROUP --log-level=debug --log-file=$LOGFILE 2>>$LOGFILE
