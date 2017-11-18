# coding: utf-8
"""
Тестовый скрипт для слежением за изменением наличия билетов на конкретный поезд.
Для отправки изменений в смс должны быть установлены переменные окружения:
TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
Twilio - сервис для отправки смс, подробнее: https://www.twilio.com/docs/api/rest

Например, проверка билетов на поезд 234Ч Москва-Няндома на 29 декабря и отправить
результат проверки на номер:
python rzd_api/check_train.py -d '2016-12-29 16:35' --to 2010220 --train 234Ч --phone +70123456789

"""
import argparse
import os
import shelve
from datetime import datetime
from traceback import print_exc

from twilio.rest import TwilioRestClient

from client import ApiClient


parser = argparse.ArgumentParser(description='Check rzd trains')
parser.add_argument('-d', dest='date', action='store', required=True,
                    help='departure datetime in format "YYYY-MM-DD HH:MM"')
parser.add_argument('--from', dest='st_from', action='store', default=2000000,
                    help='departure station code, Moscow by default')
parser.add_argument('--to', dest='st_to', action='store', required=True,
                    help='arrival station code')
parser.add_argument('--train', dest='train', action='store', required=True,
                    help='train number')
parser.add_argument('--phone', dest='phone', action='store', required=True,
                    help='phone number for sms notification')
args = parser.parse_args()

try:
    d = datetime.strptime(args.date, '%Y-%m-%d %H:%M')
except IndexError:
    print 'Wrong input date format'
    exit(1)


try:
    client = ApiClient()
    data = client.get_tickets(d, args.st_from, args.st_to, args.train)
    cars = set((c['cnumber'], c['places']) for c in data)
except Exception as e:
    print_exc()
    exit(1)


def send_message(number, body):
    client = TwilioRestClient(os.getenv('TWILIO_CLIENT_ID'),
                              os.getenv('TWILIO_CLIENT_SECRET'))
    print '[%s] Message sent!' % datetime.now()
    client.messages.create(to=number, from_=os.getenv('TWILIO_PHONE_NUMBER'), body=body)

suffix = '%s-%s-%s-%s' % (args.date, args.st_from, args.st_to, args.train)
slv = shelve.open('/tmp/rzd_cars-%s.slv' % suffix)
prev_value = slv.get('cars') or set()
print '[%s] Prev value %s, current %s!' % (datetime.now(), prev_value, cars)

if prev_value != cars:
    body = 'Tickets change! '
    if cars:
        body += 'Cars (%s): %s' % (len(cars), ', '.join(('%s: %s' % (c[0], c[1]) for c in cars))[:100])
    else:
        body += 'No seats anymore :('
    print body

    if args.phone:
        try:
            send_message(args.phone, body)
        except Exception as e:
            print '[%s] Cannot send sms!' % datetime.now()
            print_exc()

    slv['cars'] = cars
    slv.close()

