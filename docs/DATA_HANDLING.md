# Production Data Handling

## Repository boundary

This repository contains application code, schema-only documentation, and non-sensitive examples only. Do **not** commit customer SQL exports, SQLite databases, `.env` files, uploaded images, or API credentials.

## Approved EC2 locations

- Raw SQL import: `/opt/littlelabs-data/import/g5_write_counseling2.sql`
- Generated vector databases: `/opt/littlelabs-data/vector-db/`

The raw export is root-owned with mode `0600`. Access through SSM is restricted to authorized operators.

## Building a vector database

```bash
python build_vector_db.py \
  --input-sql /opt/littlelabs-data/import/g5_write_counseling2.sql \
  --output-db /opt/littlelabs-data/vector-db/counseling_vectors.db
```

The generated database may contain customer data and must not be committed to Git.
