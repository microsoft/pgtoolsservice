# DiskANN Extension for PostgreSQL

DiskANN is a scalable algorithm for approximate nearest neighbor search, enabling efficient vector search for large datasets. The `pg_diskann` extension integrates DiskANN with PostgreSQL for indexing and searching vector data.

## Enabling `pg_diskann`
1. Check that both `pg_diskann` and `vector` extensions are in the allowed extensions list for your Azure PostgreSQL server. If not
add them to the allow list.
2. Once `pg_diskann` and `vector` are in the allow list for the server, you can use either:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_diskann CASCADE;
   ```

   to create both extensions.

## Creating and Using DiskANN Index
1. Create a table with a vector column:
   ```sql
   CREATE TABLE demo (
       id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
       embedding public.vector(3)
   );
   INSERT INTO demo (embedding) VALUES
       ('[1.0, 2.0, 3.0]'),
       ('[4.0, 5.0, 6.0]'),
       ('[7.0, 8.0, 9.0]');
   ```
2. Create a DiskANN index using cosine distance:
   ```sql
   CREATE INDEX demo_embedding_diskann_idx
   ON demo USING diskann (embedding vector_cosine_ops);
   ```
3. Query for nearest neighbors:
   ```sql
   SELECT id, embedding
   FROM demo
   ORDER BY embedding <=> '[2.0, 3.0, 4.0]'
   LIMIT 5;
   ```
4. Force index usage if needed:
   ```sql
   BEGIN;
   SET LOCAL enable_seqscan TO OFF;
   -- Query
   COMMIT;
   ```

## Parallelized Index Creation
1. Enable parallel workers when creating a table:
   ```sql
   CREATE TABLE demo (
       id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
       embedding public.vector(3)
   ) WITH (parallel_workers = 4);
   ALTER TABLE demo SET (parallel_workers = 8);
   ```
2. Create an index with parallel workers:
   ```sql
   CREATE INDEX demo_embedding_diskann_idx
   ON demo USING diskann (embedding vector_cosine_ops);
   ```
3. Configure parallelization parameters:
   ```sql
   SET max_parallel_workers = 8;
   SET max_worker_processes = 8; -- Requires restart
   SET max_parallel_maintenance_workers = 4;
   ```

## Index Configuration Parameters
1. Index parameters:
   - `max_neighbors` (default: 32): Maximum edges per graph node.
   - `l_value_ib` (default: 100): Size of the search list during index build.
   ```sql
   CREATE INDEX demo_embedding_diskann_custom_idx
   ON demo USING diskann (embedding vector_cosine_ops)
   WITH (max_neighbors = 48, l_value_ib = 100);
   ```
2. Extension parameters:
   - `diskann.iterative_search` (default: `relaxed_order`): Search behavior.
     - Options: `relaxed_order`, `strict_order`, `off`.
     ```sql
     SET diskann.iterative_search TO 'strict_order';
     BEGIN;
     SET LOCAL diskann.iterative_search TO 'strict_order';
     COMMIT;
     ```
   - `diskann.l_value_is` (default: 100): L value for index scanning.
     ```sql
     SET diskann.l_value_is TO 20;
     BEGIN;
     SET LOCAL diskann.l_value_is TO 20;
     COMMIT;
     ```

## Recommended Parameter Configurations
| Dataset size | Parameter Type | Name              | Recommended Value |
|--------------|----------------|-------------------|-------------------|
| <1M          | Index build    | `l_value_ib`      | 100               |
| <1M          | Index build    | `max_neighbors`   | 32                |
| <1M          | Query time     | `diskann.l_value_is` | 100           |
| 1M-50M       | Index build    | `l_value_ib`      | 100               |
| 1M-50M       | Index build    | `max_neighbors`   | 64                |
| 1M-50M       | Query time     | `diskann.l_value_is` | 100           |
| >50M         | Index build    | `l_value_ib`      | 100               |
| >50M         | Index build    | `max_neighbors`   | 96                |
| >50M         | Query time     | `diskann.l_value_is` | 100           |

## Monitoring Index Creation Progress
Check progress using `pg_stat_progress_create_index`:
```sql
SELECT phase, round(100.0 * blocks_done / nullif(blocks_total, 0), 1) AS "%"
FROM pg_stat_progress_create_index;
```

## Supported Distance Operators
- `vector_l2_ops`: `<->` (Euclidean distance).
- `vector_cosine_ops`: `<=>` (Cosine distance).
- `vector_ip_ops`: `<#>` (Inner product).

## Troubleshooting
1. **Error: `diskann index needs to be upgraded to version 2...`**:
   - Use `REINDEX` or `REINDEX CONCURRENTLY`.
   - Upgrade index using:
     ```sql
     SELECT upgrade_diskann_index('demo_embedding_diskann_custom_idx');
     ```
   - Upgrade all DiskANN indexes:
     ```sql
     SELECT upgrade_diskann_index(pg_class.oid)
     FROM pg_class
     JOIN pg_am ON (pg_class.relam = pg_am.oid)
     WHERE pg_am.amname = 'diskann';
     ```
"  
