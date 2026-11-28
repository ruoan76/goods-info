-- 合成测试库结构。只服务 goods_mdm_test，不代表生产基线。
\set ON_ERROR_STOP on

CREATE TABLE public.sys_user (
  id              bigserial PRIMARY KEY,
  account         text NOT NULL UNIQUE,
  display_name    text NOT NULL,
  role            text NOT NULL CHECK (role IN ('Viewer','Operator','Steward')),
  status          text NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
  phone           text,
  dept            text,
  password_hash   text NOT NULL,
  last_login      timestamptz,
  token_version   integer NOT NULL DEFAULT 0,
  failed_attempts integer NOT NULL DEFAULT 0,
  locked_until    timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.sys_unit (
  code        text PRIMARY KEY,
  name        text NOT NULL,
  sort_order  integer NOT NULL DEFAULT 0,
  enabled     boolean NOT NULL DEFAULT true,
  goods_count bigint NOT NULL DEFAULT 0,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.sys_change_log (
  log_id      bigserial PRIMARY KEY,
  batch_id    text NOT NULL,
  entity_type text NOT NULL,
  entity_key  text NOT NULL,
  action      text NOT NULL,
  operator    text NOT NULL,
  before_data jsonb,
  after_data  jsonb,
  changed_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.sys_attr_template (
  id          bigserial PRIMARY KEY,
  category_id text NOT NULL UNIQUE,
  template    jsonb NOT NULL,
  enabled     boolean NOT NULL DEFAULT true,
  updated_by  text NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.sys_import_job (
  id           bigserial PRIMARY KEY,
  batch_id     text NOT NULL UNIQUE,
  job_type     text NOT NULL,
  operator     text NOT NULL,
  total_rows   integer NOT NULL DEFAULT 0,
  success_rows integer NOT NULL DEFAULT 0,
  fail_rows    integer NOT NULL DEFAULT 0,
  fail_detail  jsonb,
  status       text NOT NULL DEFAULT 'RUNNING'
               CHECK (status IN ('RUNNING','SUCCESS','PARTIAL','FAILED')),
  created_at   timestamptz NOT NULL DEFAULT now(),
  finished_at  timestamptz
);

CREATE TABLE public.sys_gov_batch (
  batch_id      text PRIMARY KEY,
  batch_type    text NOT NULL,
  rule_version  text,
  input_rows    integer,
  output_rows   integer,
  recategorized_rows integer,
  started_at    text,
  finished_at   text,
  status        text NOT NULL,
  remark        text
);

CREATE TABLE public.mdm_category (
  category_id    text PRIMARY KEY,
  parent_id      text,
  category_level integer NOT NULL,
  category_name  text NOT NULL,
  is_leaf        boolean NOT NULL DEFAULT true,
  sort_order     integer NOT NULL DEFAULT 0,
  status         text NOT NULL DEFAULT 'ACTIVE',
  version        integer NOT NULL DEFAULT 1
);

CREATE TABLE public.mdm_goods (
  barcode          text PRIMARY KEY,
  goods_name       text NOT NULL,
  category_id      text,
  category_path    text,
  category_source  text,
  unit_id          text,
  inprice          numeric(14,2),
  outprice         numeric(14,2),
  quality_grade    text NOT NULL DEFAULT 'C' CHECK (quality_grade IN ('A','B','C','D')),
  quality_score    numeric,
  status           text NOT NULL DEFAULT 'ACTIVE'
                   CHECK (status IN ('ACTIVE','INACTIVE','VOIDED')),
  version          integer NOT NULL DEFAULT 1,
  governance_batch text,
  created_at       text,
  updated_at       text
);

CREATE TABLE public.mdm_goods_history (
  id         bigserial PRIMARY KEY,
  barcode    text NOT NULL,
  field_name text NOT NULL,
  old_value  text,
  new_value  text,
  rule_code  text,
  batch_id   text NOT NULL REFERENCES public.sys_gov_batch(batch_id),
  changed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.mdm_goods_attrs (
  barcode    text PRIMARY KEY,
  attrs_json jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.mdm_barcode_alias (
  alias_barcode  text NOT NULL,
  master_barcode text NOT NULL,
  alias_type     text NOT NULL,
  banned_until   date,
  created_at     text,
  PRIMARY KEY (alias_barcode, alias_type)
);

CREATE TABLE public.dq_quarantine (
  quarantine_id bigserial PRIMARY KEY,
  batch_id      text,
  barcode       text,
  issue_type    text,
  conflict_field text,
  value_a       text,
  value_b       text,
  status        text NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.sys_field_dict (
  dict_id      bigserial PRIMARY KEY,
  table_name   text,
  column_name  text,
  cn_name      text,
  description  text,
  data_type    text,
  value_domain text
);

CREATE TABLE public.sys_quality_snapshot (
  metric      text NOT NULL,
  value_int   integer,
  measured_at timestamptz NOT NULL DEFAULT now()
);
