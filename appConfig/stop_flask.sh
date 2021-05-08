


stop_target=`ps -ef | grep python | grep "wsgi.py" |awk '{print$2}'`
for each_target in $stop_target; do
    kill -9 $each_target
done
