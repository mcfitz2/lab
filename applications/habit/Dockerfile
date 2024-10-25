FROM python:3.11
WORKDIR /code
COPY requirements.txt /code
RUN pip install -r requirements.txt
ENV PYTHONUNBUFFERED=1
COPY * /code/
ENTRYPOINT ["python", "main.py"]
