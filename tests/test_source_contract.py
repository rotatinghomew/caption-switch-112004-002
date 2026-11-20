import csv
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / "records"


class SourceContract(unittest.TestCase):
    def test_export_shape(self):
        self.assertLessEqual(set(EXPECTED), {path.name for path in ROOT.iterdir()})
        for name, contract in EXPECTED.items():
            with self.subTest(source=name):
                path = ROOT / name
                if path.suffix == ".csv":
                    with path.open(encoding="utf-8", newline="") as source:
                        reader = csv.DictReader(source)
                        self.assertEqual(reader.fieldnames, contract)
                        rows = list(reader)
                    self.assertTrue(rows)
                    self.assertTrue(all(None not in row and None not in row.values() for row in rows))
                else:
                    body = json.loads(path.read_text(encoding="utf-8"))
                    self.assertIsInstance(body, list if contract == "list" else dict)
                    self.assertTrue(body)

    def test_related_export_records(self):
        for name, value in SEQUENCE.items():
            with self.subTest(source=name):
                path = ROOT / name
                if path.suffix == ".csv":
                    with path.open(encoding="utf-8", newline="") as source:
                        cells = {cell for row in csv.reader(source) for cell in row}
                else:
                    rows = json.loads(path.read_text(encoding="utf-8"))
                    cells = {item for row in rows for item in row.values() if isinstance(item, str)}
                self.assertIn(value, cells)


EXPECTED = {'policy.json': 'dict', 'program.csv': ['block', 'window', 'chain', 'start', 'end', 'planned'], 'routes.csv': ['door', 'chain', 'cache', 'start', 'end', 'ready_at'], 'sessions.csv': ['id', 'door', 'entered', 'watched', 'reported', 'exposed', 'delay_ms', 'gap_s', 'reported_at'], 'observability.csv': ['feed', 'start', 'end', 'state', 'known_at'], 'controls.csv': ['at', 'control', 'kind', 'chain', 'action', 'origin', 'status']}
SEQUENCE = {'routes.csv': 'cache1', 'observability.csv': 'outage', 'controls.csv': 'failed'}
