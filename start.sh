ps -ef | grep uwsgi |awk '{print $2}' | xargs kill -9
uwsgi --ini ./uwsgi.ini
