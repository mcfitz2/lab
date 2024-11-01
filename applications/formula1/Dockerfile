FROM python:3.9
ADD requirements.txt /code/requirements.txt
WORKDIR /code
RUN pip install -r requirements.txt
ADD . /code
CMD python main.py
