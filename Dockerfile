FROM python:3.11
WORKDIR /app
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
COPY ./nginx ./nginx
COPY ./src ./src
COPY ./static ./static
COPY ./templates ./templates
CMD ["python3", "-m", "src.main", "--host", "0.0.0.0"]
