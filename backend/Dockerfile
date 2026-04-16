# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    # Add dependencies for WeasyPrint (libpangocairo pulls in pango, cairo, and gobject)
    libpangocairo-1.0-0 \
    # Add dependencies for OpenCV (cv2)
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libxrender1 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy the rest of the application's code into the container
COPY . /app

# The command to run the application will be specified in docker-compose.yml 