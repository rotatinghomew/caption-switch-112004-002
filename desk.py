import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit


PATH = re.compile(r'/desk/(dispatcher|backup)/operations/([a-zA-Z0-9_-]+)')
FIELDS = {'operation', 'route_gen', 'chain', 'mode', 'start', 'end', 'scope', 'station'}


def desk_server(state, address):
    database = sqlite3.connect(state)
    database.execute('CREATE TABLE IF NOT EXISTS calls (desk TEXT, ident TEXT, body TEXT, '
                     'PRIMARY KEY (desk, ident))')
    database.execute('CREATE TABLE IF NOT EXISTS receipts (seq INTEGER PRIMARY KEY, desk TEXT, '
                     'ident TEXT, body TEXT)')

    class Desk(BaseHTTPRequestHandler):
        def answer(self, status, value):
            raw = json.dumps(value, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def location(self):
            path = urlsplit(self.path).path
            parent = PATH.fullmatch(path.removesuffix('/receipts'))
            if parent is None:
                return None, False
            return parent.groups(), path.endswith('/receipts')

        def read_json(self):
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 32768:
                raise ValueError
            value = json.loads(self.rfile.read(size))
            if not isinstance(value, dict):
                raise ValueError
            return value

        def do_GET(self):
            key, receipts = self.location()
            if key is None:
                return self.answer(404, {'error': '路径不存在'})
            row = database.execute('SELECT body FROM calls WHERE desk=? AND ident=?', key).fetchone()
            if row is None:
                return self.answer(404, {'error': '该台未登记此号'})
            events = database.execute('SELECT body FROM receipts WHERE desk=? AND ident=? ORDER BY seq', key)
            payload = [json.loads(event[0]) for event in events]
            self.answer(200, payload if receipts else {'request': json.loads(row[0]), 'receipts': payload})

        def do_PUT(self):
            key, receipts = self.location()
            if key is None or receipts:
                return self.answer(404, {'error': '路径不存在'})
            try:
                request = self.read_json()
                if set(request) != FIELDS or request['operation'] != key[1]:
                    raise ValueError
                if request['station'] != key[0]:
                    raise ValueError
            except (ValueError, TypeError):
                return self.answer(400, {'error': '交接格式错误'})
            raw = json.dumps(request, ensure_ascii=False, sort_keys=True)
            old = database.execute('SELECT body FROM calls WHERE desk=? AND ident=?', key).fetchone()
            if old and old[0] != raw:
                return self.answer(409, {'error': '该台的操作号已有另一份正文'})
            if not old:
                with database:
                    database.execute('INSERT INTO calls VALUES (?, ?, ?)', (*key, raw))
                if self.headers.get('X-Desk-Simulation') == 'drop-acceptance':
                    self.close_connection = True
                    return
            self.answer(202, {'operation': key[1], 'station': key[0], 'kind': 'registered'})

        def do_POST(self):
            key, receipts = self.location()
            if key is None or not receipts:
                return self.answer(404, {'error': '路径不存在'})
            if database.execute('SELECT 1 FROM calls WHERE desk=? AND ident=?', key).fetchone() is None:
                return self.answer(404, {'error': '该台未登记此号'})
            try:
                event = self.read_json()
                if set(event) != {'at', 'effective_at', 'kind', 'route_gen'}:
                    raise ValueError
                if event['kind'] not in ('accepted', 'applied', 'rejected'):
                    raise ValueError
                if (event['kind'] == 'applied') != (event['effective_at'] is not None):
                    raise ValueError
            except (ValueError, TypeError):
                return self.answer(400, {'error': '台端回执格式错误'})
            event.update(operation=key[1], station=key[0])
            with database:
                database.execute('INSERT INTO receipts(desk, ident, body) VALUES (?, ?, ?)',
                                 (*key, json.dumps(event, ensure_ascii=False)))
            self.answer(201, event)

    server = HTTPServer(address, Desk)
    return server, database


def main():
    parser = argparse.ArgumentParser(description='两个演练调度台的来件箱')
    parser.add_argument('--state', type=Path, required=True, help='保存台端往来的 SQLite 文件')
    parser.add_argument('--port', type=int, default=8087)
    args = parser.parse_args()
    server, database = desk_server(args.state, ('127.0.0.1', args.port))
    try:
        server.serve_forever()
    finally:
        server.server_close()
        database.close()


if __name__ == '__main__':
    main()
