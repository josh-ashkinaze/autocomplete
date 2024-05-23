FROM python:3.9-slim
WORKDIR /myapp
COPY ./requirements.txt /myapp
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8080"]
