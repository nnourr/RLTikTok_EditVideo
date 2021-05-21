FROM python:3.9

WORKDIR /editVideo

ENV PYTHONUNBUFFERED True

ADD editVideo editVideo

ENV PORT 8080

COPY requirements.txt .

# Install numpy using system package manager
RUN apt-get -y update && apt-get -y install ffmpeg imagemagick libopencv-dev python-opencv

RUN pip install -r requirements.txt

CMD [ "python", "editVideo/videoEditor.py" ]