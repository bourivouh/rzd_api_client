# coding: utf-8
from time import sleep

import requests


class ApiClient(object):
    """ Клиент для апи РЖД
    """
    # TODO получение кодов станций по названию, пока что приходится вытаскивать с сайта
    # TODO структурированный ответ, а выдача всего мусора, что отдает апишка
    # TODO сделать клиент отдельным пакетом

    BASE_URL = 'https://pass.rzd.ru/timetable/public/ru'
    STRUCTURE_ID = 735

    LAYER_TRAINS = 5371
    LAYER_TRAIN_TICKETS = 5373

    class ResponseError(Exception):
        pass

    def get_timetable(self, date, station_from, station_to):
        """ Информацию о расписании поездов на конкретный день

        :param date: дата отправления, объект date/datetime
        :param station_from: код станции отправления, строка
        :param station_to: код станции назначения, строка
        """
        params = {
            'layer_id': self.LAYER_TRAINS,
            'dir': 0,
            'tfl': 3,
            'checkSeats': 0,
            'withoutSeats': 'y',
            'code0': station_from,
            'code1': station_to,
            'dt0': date.strftime('%d.%m.%Y')
        }
        return self.request('get', params=params)

    def get_tickets(self, date, station_from, station_to, train):
        """ Информация о билетах на конретный поезд

        :param date: дата и время отправления, объект datetime
        :param station_from: код станции отправления, строка
        :param station_to: код станции назначения, строка
        :param train: номер поезда, строка

        :return: список вагонов с доступными билетами
        """
        params = {
            'layer_id': self.LAYER_TRAIN_TICKETS
        }
        data = {
            'dir': 0,
            'code0': station_from,
            'code1': station_to,
            'trDate0': date.strftime('%d.%m.%Y %H:%M'),
            'tnum0': train,
            'dt0': date.strftime('%d.%m.%Y')
        }
        response = self.request('post', params=params, data=data)
        return [car for l in response.get('lst', []) for car in l.get('cars', [])]

    def request(self, method_name='get', params=None, data=None):
        params = params or {}
        params.setdefault('structure_id', self.STRUCTURE_ID)

        with self._get_session() as s:
            method = getattr(s, method_name)
            # У ржд сложная схема. Сначала нужно выполнить запрос со всеми данными,
            # но без параметра rid (request id?). Если всё ок, то в ответ
            # вернется этот самый параметр, его подставляем в запрос и
            # уже можем идти за искомыми данными
            response_data = self._do_request(method, params, data)
            rid = response_data.get('rid', response_data.get('RID'))
            if not rid:
                raise self.ResponseError()

            if data:
                data['rid'] = rid
            else:
                params['rid'] = rid

            # у них не сразу могут долетать данные о созданном rid, поэтому перед
            # вторым запросом нужно чуть подождать
            sleep(1)
            return self._do_request(method, params=params, data=data)

    def _do_request(self, method, params=None, data=None):
        res = method(self.BASE_URL, params=params, data=data)
        # TODO добавить проверку ответа на ошибки
        if not res.ok:
            raise self.ResponseError()
        return res.json()

    def _get_session(self):
        if not hasattr(self, '_session'):
            self._session = requests.Session()
            self._session.cookies['JSESSIONID'] = self._gen_sid()
        return self._session

    def _gen_sid(self):
        """ Генерирует session_id
        """
        # TODO понять как формируется сессия и сделать нормальную генерациюы
        return '00006mwFi5RKtF-z0R16OGSMJtS:17obqce3m'
