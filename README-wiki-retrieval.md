# Customer Q&A Wiki retrieval

The application can retrieve customer knowledge from a read-only Wiki directory without creating a dedicated iCloud vector database.

## Runtime path

Set `CUSTOMER_QNA_WIKI_PATH` to the mounted Wiki path. The compose configuration mounts `./wiki` to `/app/data/wiki` read-only, which is also the default path used by `agent.py`.

## What is searched

1. Approved customer Q&A pages (`concepts/` or `entities/`) require:
   - `brand: littlelabs | thelittles | puregen | greenroot`
   - `status: approved`
   - `qna_export: true`
   - `### Q: ...` / `A: ...` format
2. During migration, source files in `raw/icloud/` may be searched only when their frontmatter explicitly says `customer_search: true`. Other raw folders, including `raw/openviking/`, are never searched.

The retriever uses keyword/token overlap and limits raw-source context to 1,800 characters per result. It has no SQLite/vector DB or embedding dependency.

## Review workflow

`raw/icloud/` source → reviewed page in `concepts/` or `entities/` → add brand/status/`qna_export: true` → Wiki keyword retrieval.

Once a reviewed page replaces an iCloud source, set the source page's `customer_search: false` so only the approved Q&A is used.
