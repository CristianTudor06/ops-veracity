FROM python:3.11.3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./model/detector_model ./model/detector_model
COPY ./app .

EXPOSE 8000