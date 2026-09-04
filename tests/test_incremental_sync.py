"""TDD test for incremental Naver sync: existing answered items must be skipped.

Runs INSIDE the littlelabs-qna container at /app with PYTHONPATH=/app.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import naver_api_agent as naa


class FakeVector:
    def tolist(self):
        return [0.0, 0.0, 0.0, 1.0]


class FakeModel:
    def get_sentence_embedding_dimension(self):
        return 4

    def encode(self, text, normalize_embeddings=True):
        return FakeVector()


def make_db(path, ids):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 " inquiry_id TEXT, chunk_text TEXT, product_name TEXT, subject TEXT,"
                 " is_answered INTEGER, embedding BLOB)")
    for i in ids:
        conn.execute("INSERT INTO chunks (inquiry_id, chunk_text, product_name, subject,"
                     " is_answered, embedding) VALUES (?, 'x', 'p', 's', 1, X'00')", (i,))
    conn.commit()
    conn.close()


class IncrementalSyncTest(unittest.TestCase):
    def test_get_existing_inquiry_ids_returns_stored_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'v.db'
            make_db(p, ['100', '200'])
            self.assertEqual(naa.get_existing_inquiry_ids(str(p)), {'100', '200'})

    def test_missing_db_returns_empty_set(self):
        self.assertEqual(naa.get_existing_inquiry_ids('/nonexistent/x.db'), set())

    def test_process_and_save_skips_existing_answered_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'v.db'
            make_db(p, ['100'])
            existing_item = {'questionId': '100', 'productName': 'X', 'title': 't',
                             'content': 'c', 'isAnswered': True}
            new_item = {'questionId': '999', 'productName': 'Y', 'title': 't2',
                        'content': 'c2', 'isAnswered': True}

            with patch.object(naa, 'fetch_recent_inquiries', return_value=[existing_item, new_item]), \
                 patch.object(naa, 'get_db_path', return_value=str(p)), \
                 patch.object(naa, 'load_embedding_model', return_value=FakeModel()), \
                 patch.object(naa, 'embedding_to_bytes', return_value=b'abcd'):
                ok, inserted, updated = naa.process_and_save('puregen', incremental=True)
            self.assertTrue(ok)
            self.assertEqual(inserted, 1, 'only the new item should be embedded')
            self.assertEqual(updated, 0, 'existing answered item should be skipped')


if __name__ == '__main__':
    unittest.main()
