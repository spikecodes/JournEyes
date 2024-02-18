# Use an official Python runtime as a parent image
FROM python:3.9-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Use an official Python runtime as a base image
FROM python:3.9-slim

# Create and switch to a new user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Copy the built wheels from the builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install the app dependencies
RUN pip install --no-cache /wheels/*

# Copy only the directories and files you need
COPY --chown=appuser:appuser ./segment_anything ./segment_anything
COPY --chown=appuser:appuser ./lang_sam ./lang_sam
COPY --chown=appuser:appuser ./*.py ./

# Your FastAPI app command to run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4008"]
