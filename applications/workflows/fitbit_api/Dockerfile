# We're using the latest version of Prefect with Python 3.10
FROM prefecthq/prefect:2-python3.11
RUN apt-get update && apt-get install -y libmariadb3 libmariadb-dev

# Add our requirements.txt file to the image and install dependencies
COPY ./requirements.txt .
RUN pip install -r requirements.txt --trusted-host pypi.python.org --no-cache-dir

# Add our flow code to the image
COPY ./fitbit_api /opt/prefect/flows
COPY ./common-libs/python/common.py /opt/prefect/flows

# Run our flow script when the container starts
CMD ["python", "flows/master_flow.py"]