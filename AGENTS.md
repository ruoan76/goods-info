# Project layout rules

- `/data/projects/goods-info` is the only project root.
- Application code belongs under `apps/`.
- Database migrations and maintenance SQL belong under `db/`.
- Governance code belongs under `governance/`. Historical scripts stay under `governance/scripts/legacy` until replaced.
- Current documents belong under `docs/`. Historical documents belong under `docs/archive/`.
- Deploy and backup templates belong under `ops/`.
- Runtime data, virtual environments, build output, backups and generated evidence belong under `data/` or `reports/` and are ignored by Git.
- Do not add database passwords to source files. Inject `GOODS_MDM_PG_DSN`, `PG_DSN_APP`, `PG_DSN_RO` and `JWT_SECRET` through the runtime environment.
- The `08_治理执行` directory is a compatibility entry point. New references must use canonical paths.
