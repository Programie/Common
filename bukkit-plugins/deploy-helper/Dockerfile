FROM python:3

COPY requirements.txt /requirements.txt

RUN pip3 install -r /requirements.txt

COPY deploy.py /deploy.py

CMD ["/bin/bash"]