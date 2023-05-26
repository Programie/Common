FROM python:3

COPY requirements.txt /requirements.txt

RUN pip3 install -r /requirements.txt && \
    curl -L -o /usr/local/bin/release-cli https://release-cli-downloads.s3.amazonaws.com/latest/release-cli-linux-amd64 && \
    chmod +x /usr/local/bin/release-cli

COPY deploy.py /deploy.py

CMD ["/bin/bash"]