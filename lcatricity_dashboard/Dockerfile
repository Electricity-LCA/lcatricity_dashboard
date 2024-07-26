FROM python:3.12.3-slim-bullseye

ENTRYPOINT ["top", "-b"]

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

COPY ../requirements.txt /usr/src/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
