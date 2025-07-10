FROM python:3.13.5-alpine3.22
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apk add --no-cache git

COPY . ./CROUStillantBackup

WORKDIR /CROUStillantBackup

RUN uv sync --frozen --no-dev

RUN crontab crontab

CMD ["crond", "-f"]
