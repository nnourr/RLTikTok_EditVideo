FROM python:3.9

WORKDIR /funcDownloadRL

ENV PYTHONUNBUFFERED True

ADD funcDownloadRL funcDownloadRL

ENV PORT 8080

COPY requirements.txt .

# Install numpy using system package manager
RUN apt-get -y update && apt-get -y install ffmpeg imagemagick libopencv-dev python-opencv

# RUN apt-get install -y locales && \
#     locale-gen C.UTF-8 && \
#     /usr/sbin/update-locale LANG=C.UTF-8

RUN pip install -r requirements.txt

CMD [ "python", "funcDownloadRL/redditDownload.py" ]