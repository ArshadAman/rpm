FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_ROOT_USER_ACTION=ignore

RUN adduser -D myuser
USER myuser
WORKDIR /home/myuser

COPY --chown=myuser:myuser requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

ENV PATH="/home/myuser/.local/bin:${PATH}"

COPY --chown=myuser:myuser . .

# WORKDIR /app

# COPY requirements.txt /app/
# RUN pip install --upgrade pip && pip install -r requirements.txt

# COPY . /app/

# Create logs directory
RUN mkdir -p /app/logs

CMD ["gunicorn", "rpm.wsgi:application", "--bind", "0.0.0.0:8000"]