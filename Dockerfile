FROM python:3.8-alpine

RUN apk --no-cache add git

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./git_mirror /app/git_mirror

WORKDIR /app

CMD ["python3", "-m", "git_mirror"]
