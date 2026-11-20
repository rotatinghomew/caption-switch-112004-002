import csv
import json
from pathlib import Path
import unittest


RECORDS = Path(__file__).resolve().parents[1] / 'records'
SCHEMAS = {'next_program.csv': ['cycle', 'pair', 'chain', 'cache', 'scope', 'start', 'end', 'planned', 'signed_at', 'route_gen'], 'handoffs.json': 'dict'}


class PartnerSourceTests(unittest.TestCase):
    def test_format(self):
        for name, shape in SCHEMAS.items():
            with self.subTest(name=name), (RECORDS / name).open(encoding='utf-8', newline='') as source:
                if isinstance(shape, list):
                    rows = csv.DictReader(source)
                    self.assertEqual(rows.fieldnames, shape)
                    records = list(rows)
                    self.assertTrue(records)
                    self.assertTrue(all(None not in row and None not in row.values() for row in records))
                else:
                    records = json.load(source)
                    self.assertIsInstance(records, list if shape == 'list' else dict)
                    self.assertTrue(records)
