FROM python:3.11.3

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

# Copy your entire project directory into /code
# This includes the 'app' directory, 'model' directory, etc.
COPY . /code/

EXPOSE 8000