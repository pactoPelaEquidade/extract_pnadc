FROM python:3.9-alpine

COPY ./ ./
RUN apk update && apk add bash && apk add --no-cache make && apk add g++
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt
CMD ["python", "extract.py"]