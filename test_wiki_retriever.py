import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "wiki_retriever", Path(__file__).with_name("wiki_retriever.py")
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def write_page(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_returns_only_explicitly_approved_pages_for_matching_brand(tmp_path):
    wiki = tmp_path / "wiki"
    write_page(
        wiki / "concepts" / "littlelabs-growth.md",
        """---
brand: littlelabs
qna_export: true
status: approved
tags: [nutrition, intake]
---
### Q: 아이 키 영양제는 언제 먹나요?
A: 제품 라벨의 섭취 방법을 따르세요.
""",
    )
    write_page(
        wiki / "concepts" / "internal.md",
        """---
brand: littlelabs
qna_export: false
status: reviewed
tags: [process]
---
### Q: 내부 절차는?
A: 고객에게 공개하면 안 됩니다.
""",
    )
    write_page(
        wiki / "concepts" / "other-brand.md",
        """---
brand: puregen
qna_export: true
status: approved
tags: [nutrition]
---
### Q: 키 영양제는?
A: 다른 브랜드 답변입니다.
""",
    )

    hits = module.search_customer_qna(wiki, "littlelabs", "아이 키 영양제 섭취", top_k=3)

    assert len(hits) == 1
    assert hits[0]["source"] == "concepts/littlelabs-growth.md"
    assert hits[0]["question"] == "아이 키 영양제는 언제 먹나요?"


def test_matches_korean_substring_terms_and_ranks_best_hit_first(tmp_path):
    wiki = tmp_path / "wiki"
    write_page(
        wiki / "concepts" / "growth.md",
        """---
brand: littlelabs
qna_export: true
status: approved
tags: [nutrition, intake]
---
### Q: 키 영양제는 어떻게 먹나요?
A: 성장기 영양 관리는 제품 라벨을 확인하세요.
""",
    )
    write_page(
        wiki / "concepts" / "digestion.md",
        """---
brand: littlelabs
qna_export: true
status: approved
tags: [nutrition]
---
### Q: 소화가 불편해요.
A: 개인 상태에 따라 전문가 상담이 필요할 수 있습니다.
""",
    )

    hits = module.search_customer_qna(wiki, "littlelabs", "키 영양제 어떻게 먹나요", top_k=3)

    assert [hit["source"] for hit in hits] == ["concepts/growth.md"]


def test_returns_no_result_when_no_approved_customer_qa_matches(tmp_path):
    wiki = tmp_path / "wiki"
    write_page(
        wiki / "raw" / "icloud" / "raw-note.md",
        """---
brand: littlelabs
qna_export: true
---
### Q: 키 영양제는?
A: raw는 검색 대상이 아닙니다.
""",
    )

    assert module.search_customer_qna(wiki, "littlelabs", "키 영양제", top_k=3) == []
