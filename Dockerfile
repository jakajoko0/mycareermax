# Use Python 3.12 image as the base
FROM python:3.12

WORKDIR /app

# Update the system and install wkhtmltopdf and required dependencies for ODBC Driver
RUN apt-get update -y && \
    apt-get install -y wkhtmltopdf gpg apt-transport-https curl && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update -y && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    apt-get install -y unixodbc-dev

# Set the ODBC driver version in the environment variable
ENV ODBC_DRIVER_VERSION=18

# Set LD_LIBRARY_PATH environment variable
ENV LD_LIBRARY_PATH=/opt/microsoft/msodbcsql${ODBC_DRIVER_VERSION}/lib64:${LD_LIBRARY_PATH}

# Copy and install application dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Specify the command to run on container start
CMD ["python", "./app.py"]
