FROM python:3-buster

RUN apt-get update && \
  apt-get -y install git fio vim && \
  apt-get clean

RUN git clone https://github.com/louwrentius/fio-plot.git /fio-plot && \
    cd /fio-plot/fio_plot && \
    pip3 install -r requirements.txt 
