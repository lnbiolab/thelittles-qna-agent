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
A: 이 내용은 고객 답변으로 내보내면 안 됩니다.
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


def test_returns_selected_icloud_raw_sections_without_database(tmp_path):
    wiki = tmp_path / "wiki"
    write_page(
        wiki / "raw" / "icloud" / "growth.md",
        """---
source_title: 키영양제
customer_search: true
qna_export: false
---
# 키영양제

---

<복용 방법>
알약을 못 먹으면 수저 뒤로 부셔서 섭취할 수 있습니다.

---

<주의사항>
제품 라벨과 전문가 안내를 확인하세요.
""",
    )

    hits = module.search_customer_qna(wiki, "littlelabs", "키 영양제 알약 복용", top_k=3)

    assert len(hits) == 1
    assert hits[0]["source"] == "raw/icloud/growth.md"
    assert "알약을 못 먹으면" in hits[0]["chunk_text"]
    assert hits[0]["type"] == "wiki-raw"
    assert len(hits[0]["chunk_text"]) <= 1900


def test_splits_large_selected_icloud_sections_into_bounded_search_contexts(tmp_path):
    wiki = tmp_path / "wiki"
    write_page(
        wiki / "raw" / "icloud" / "large.md",
        """---
source_title: 키영양제
customer_search: true
---
""" + "키 영양제 알약 복용 방법입니다.\n\n" * 300,
    )

    hits = module.search_customer_qna(wiki, "littlelabs", "키 영양제 알약 복용", top_k=3)

    assert hits
    assert all(len(hit["chunk_text"]) <= 1900 for hit in hits)


def test_excludes_unselected_or_non_icloud_raw_sources(tmp_path):
    wiki = tmp_path / "wiki"
    write_page(
        wiki / "raw" / "icloud" / "unselected.md",
        """---
source_title: 내부 메모
customer_search: false
---
키 영양제 내부 내용
""",
    )
    write_page(
        wiki / "raw" / "openviking" / "internal.md",
        """---
customer_search: true
---
키 영양제처럼 보이는 내부 운영 내용
""",
    )

    assert module.search_customer_qna(wiki, "littlelabs", "키 영양제", top_k=3) == []


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    for test in [
        test_returns_only_explicitly_approved_pages_for_matching_brand,
        test_returns_selected_icloud_raw_sections_without_database,
        test_splits_large_selected_icloud_sections_into_bounded_search_contexts,
        test_excludes_unselected_or_non_icloud_raw_sources,
    ]:
        with TemporaryDirectory() as directory:
            test(Path(directory))
    print("3 tests passed")
