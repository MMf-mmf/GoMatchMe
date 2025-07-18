# Pull official base Python Docker image
FROM python:3.12.3
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Set work directory
WORKDIR /code

# Install dependencies
RUN pip install --upgrade pip
COPY requirements/production.txt requirements/base.txt ./

RUN pip install -r production.txt

COPY . .