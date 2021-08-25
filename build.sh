#!/bin/sh

tag="0.0"
docker build -t svallero/fio-plot:$tag .
docker push svallero/fio-plot:$tag
