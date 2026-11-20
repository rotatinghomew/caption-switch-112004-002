from http.client import HTTPConnection, RemoteDisconnected
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest

from desk import desk_server


class DeskContract(unittest.TestCase):
    def test_duplicate_registration_and_independent_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'desk.sqlite3'
            server, database = desk_server(state, ('127.0.0.1', 0))
            main_path = '/desk/dispatcher/operations/x4'
            backup_path = '/desk/backup/operations/x4'
            request = dict(operation='x4', route_gen=7, chain='stream1', mode='base',
                           start=100, end=200, scope='场内入口', station='dispatcher')

            def call(method, path, body=None, headers=None):
                client = HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                try:
                    client.request(method, path, json.dumps(body) if body is not None else None,
                                   headers or {})
                    response = client.getresponse()
                    return response.status, json.loads(response.read())
                finally:
                    client.close()

            def exercise():
                with self.assertRaises(RemoteDisconnected):
                    call('PUT', main_path, request, {'X-Desk-Simulation': 'drop-acceptance'})
                self.assertEqual(call('GET', main_path), (200, {'request': request, 'receipts': []}))
                self.assertEqual(call('GET', backup_path)[0], 404)
                self.assertEqual(call('PUT', main_path, request)[0], 202)
                self.assertEqual(call('PUT', main_path, {**request, 'mode': 'dual'})[0], 409)
                event = dict(at=105, effective_at=103, kind='applied', route_gen=7)
                self.assertEqual(call('POST', main_path + '/receipts', event)[0], 201)
                self.assertEqual(call('GET', main_path + '/receipts'),
                                 (200, [{**event, 'operation': 'x4', 'station': 'dispatcher'}]))

            error = []

            def client_job():
                try:
                    exercise()
                except Exception as failure:
                    error.append(failure)
                finally:
                    server.shutdown()

            worker = Thread(target=client_job)
            worker.start()
            try:
                server.serve_forever(poll_interval=0.01)
            finally:
                worker.join()
                server.server_close()
                database.close()
            if error:
                raise error[0]
