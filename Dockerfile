FROM python:3
ADD graylog_to_statuspage.py /
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY graylog_to_statuspage_config.yaml /var/opt/graylog_to_statuspage/graylog_to_statuspage_config.yaml
CMD [ "python", "./graylog_to_statuspage.py", "-c", "/var/opt/graylog_to_statuspage/graylog_to_statuspage_config.yaml", "-d", "-v", "-s" ]