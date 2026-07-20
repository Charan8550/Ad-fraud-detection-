# Use official python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /code

# Copy requirements and install
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and set permissions
RUN useradd -m -u 1000 user
USER user

# Set environmental variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

# Copy the rest of the application files
COPY --chown=user . /code

# Expose port 7860 for Hugging Face Spaces
EXPOSE 7860

# Run the Flask app using Gunicorn on port 7860
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--timeout", "120", "app:app"]
