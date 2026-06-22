FROM python:3.13-slim

WORKDIR /home/projects

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
