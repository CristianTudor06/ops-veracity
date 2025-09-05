FROM python:3.11.3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# This line assumes your trained model is in the 'model' directory
# We copy it into the container so the worker can access it.
COPY ./model/detector_model ./model/detector_model
COPY ./app .

# Expose the API port
EXPOSE 8000