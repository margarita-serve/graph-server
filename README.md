# Bokeh Graph Server
Bokeh Graph를 제공하는 Server

## 실행 환경설정
```shell
# drift와 accuracy 정보를 받을 서버
export DRIFT_MONITOR_ENDPOINT="http://192.168.88.151:30071"
export ACCURACY_MONITOR_ENDPOINT="http://192.168.88.151:30072"
export SERVICE_MONITOR_ENDPOINT="http://192.168.88.151:30073"
```


## 로컬환경 실행
```shell
$ python main.py
```

## Docker실행
```shell
docker run --env-file ./.env -p 8004:8004 192.168.88.155/koreserve/graph:{tag}
```

## REST-API
- For swagger document you have to request root directory(/)
```shell
http://yourhostname:8004/
```