FROM python:3.12.7-alpine3.20

COPY . ./CROUStillantBackup

WORKDIR /CROUStillantBackup

RUN pip install --no-cache-dir -r requirements.txt

RUN crontab crontab

CMD ["crond", "-f"]
