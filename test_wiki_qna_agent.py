import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.modules.setdefault("numpy", types.ModuleType("numpy"))
sentence_transformers = types.ModuleType("sentence_transformers")
sentence_transformers.SentenceTransformer = object
sys.modules.setdefault("sentence_transformers", sentence_transformers)

import agent


class WikiCustomerQnATests(unittest.TestCase):
    def make_wiki(self, root: Path) -> None:
        page = root / "concepts" / "growth.md"
        page.parent.mkdir(parents=True)
        page.write_text(
            """---
brand: littlelabs
qna_export: true
status: approved
tags: [nutrition, intake]
---
### Q: 키 영양제는 어떻게 먹나요?
A: 제품 라벨의 섭취 방법을 따르세요.
""",
            encoding="utf-8",
        )

    def test_uses_wiki_customer_qa_before_legacy_vector_db(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            "CUSTOMER_QNA_WIKI_PATH": directory,
        }, clear=True):
            self.make_wiki(Path(directory))
            qna = agent.QnAAgent()
            qna.get_retriever = lambda chat_type: self.fail("legacy DB must not be queried")

            result = qna.generate_answer("키 영양제 어떻게 먹나요", chat_type="qa_littlelabs")

        self.assertEqual(result["sources"], [{
            "subject": "키 영양제는 어떻게 먹나요?", "type": "wiki", "date": ""
        }])
        self.assertIn("제품 라벨의 섭취 방법", result["answer"])

    def test_falls_back_to_legacy_brand_db_when_wiki_has_no_match(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            "CUSTOMER_QNA_WIKI_PATH": directory,
        }, clear=True):
            qna = agent.QnAAgent()
            qna.get_retriever = lambda chat_type: types.SimpleNamespace(hybrid_search=lambda query, top_k: [{
                "wr_subject": "기존 브랜드 지식", "chunk_type": "QnA", "wr_datetime": "", "chunk_text": "기존 답변"
            }])

            result = qna.generate_answer("키 영양제 어떻게 먹나요", chat_type="qa_littlelabs")

        self.assertEqual(result["sources"], [{
            "subject": "기존 브랜드 지식", "type": "QnA", "date": ""
        }])


if __name__ == "__main__":
    unittest.main()
