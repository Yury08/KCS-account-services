FROM python:3.11.5-alpine

# Запрещает питону создавать файлы с кешом
ENV PYTHONDONTWRITEBYTECODE 1
# Логи не буферезируются
ENV PYTHONUNBUFFERED 1

RUN adduser --disabled-password --no-create-home account_service

ENV APP_HOME=/account_service

RUN mkdir $APP_HOME
WORKDIR $APP_HOME

COPY ./requirements.txt $APP_HOME

RUN pip install --root-user-action=ignore --upgrade pip
RUN pip install --root-user-action=ignore --upgrade wheel
RUN pip install --root-user-action=ignore --upgrade setuptools
RUN pip install --root-user-action=ignore -r requirements.txt

COPY . $APP_HOME

RUN chown -R account_service:account_service $APP_HOME

RUN python manage.py collectstatic --noinput

USER account_service:account_service
