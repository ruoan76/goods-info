-- ============================================================
-- 商品主数据治理 · 数据库表结构（方案一 v3.2 + 过程目录扩展 v1.0）
-- 原则：无效数据不落地 / 过程不落库只留结果 / 不建未来才用的表
-- 结果：7 张成果表（原 16 张）+ 3 张管理表（过程1+目录2，合计<200行）+ 4 个零存储视图
-- 条码规范：校验位通过才保留 / 000 补 0 去除 / EAN-8 以原生 8 位为主键，不升位
-- 售价定位：outprice = 参考价，门店实际成交价由方案二独立管理
-- 方言：MySQL 8.0 / utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS goods_mdm DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE goods_mdm;

-- ------------------------------------------------------------
-- 1. 商品主档（黄金记录）：一张表承载全部治理成果
-- ------------------------------------------------------------
CREATE TABLE mdm_goods (
  barcode          VARCHAR(32)   NOT NULL              COMMENT '规范化条码 = 商品主键（EAN-13 为 13 位；EAN-8 以原生 8 位保留，不升位；校验位均通过）',
  goods_name       VARCHAR(256)  NOT NULL              COMMENT '众数采纳名称',
  category_id      VARCHAR(16)   DEFAULT NULL          COMMENT '治理后统一末级分类 ID，关联 mdm_category',
  category_path    VARCHAR(256)  DEFAULT NULL          COMMENT '冗余物化路径 /C01/C0101/，统计分析免 JOIN',
  category_source  VARCHAR(16)   DEFAULT NULL          COMMENT '分类来源：ADOPT 投票/MAPPING 映射/AI_FILLBACK 回填/UNCLASSIFIED',
  category_confidence DECIMAL(5,4) DEFAULT NULL        COMMENT '分类置信度（AI 回填/映射时记录）',
  unit_id          VARCHAR(16)   DEFAULT NULL          COMMENT '单位编码',
  inprice          DECIMAL(18,6) DEFAULT NULL          COMMENT '众数进价（唯一值）',
  outprice         DECIMAL(18,6) DEFAULT NULL          COMMENT '众数参考价（非权威售价；门店实际价由方案二管理，扫码校准交方案二）',
  quality_grade    CHAR(1)       NOT NULL              COMMENT '质量等级 A/B/C/D',
  quality_score    DECIMAL(5,2)  DEFAULT NULL          COMMENT '质量总分（六维加权结果，明细不落库）',
  decision_trace   JSON          DEFAULT NULL          COMMENT '决策依据：每字段记采纳值/来源/规则，冲突字段多记票数；血缘载体，不另建投票表',
  governance_batch VARCHAR(32)   NOT NULL              COMMENT '产出该记录的治理批次',
  version          INT           NOT NULL DEFAULT 1    COMMENT '版本号（回滚靠批次重跑，不逐字段留日志）',
  status           VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/QUARANTINED/DISABLED',
  created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (barcode),
  KEY idx_category (category_id),
  KEY idx_catpath (category_path(64)),
  KEY idx_grade (quality_grade, quality_score),
  KEY idx_batch (governance_batch)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品主档黄金记录：446 万条，治理最终成果';

-- decision_trace 结构示例（一致字段记来源，冲突字段多记票数/规则）：
-- {"GOODS_NAME":{"v":"康师傅红烧牛肉面","src":"goods_csv","rule":"MODE"},
--  "OUTPRICE":{"v":3.5,"src":"goods_csv","votes":"1:1","rule":"TIE_C4_MEDIAN"},
--  "SORT_ID":{"v":"03000001","src":"goods_csv","rule":"MAPPING"}}
-- 说明：这张 JSON 就是治理与管理之间的血缘契约，方案二直接续记/读取，不另建投票表。

-- ------------------------------------------------------------
-- 2. 分类维表：N 级分类树 + 物化路径（统计分析与维护管理的核心）
--    分类码体系：02xxxxxx 大类 / 03xxxxxx 末级 / 01999999 未分类
-- ------------------------------------------------------------
CREATE TABLE mdm_category (
  category_id      VARCHAR(16)   NOT NULL              COMMENT '分类主键（内部生成），统计分析稳定锚点',
  parent_id        VARCHAR(16)   DEFAULT NULL          COMMENT '父分类，根为 NULL',
  category_level   TINYINT       NOT NULL              COMMENT '层级 1=大类 2=末级，可扩展 N 级',
  category_path    VARCHAR(256)  NOT NULL              COMMENT '物化路径 /C01/C0101/，按前缀一次查任意层级子孙',
  category_name    VARCHAR(64)   NOT NULL              COMMENT '分类名称',
  external_code    VARCHAR(16)   DEFAULT NULL          COMMENT '旧编码 02000001/03000001，兼容下游与来源映射',
  is_leaf          TINYINT       NOT NULL DEFAULT 1    COMMENT '是否末级（可挂商品）1是/0否',
  sort_order       INT           NOT NULL DEFAULT 0    COMMENT '同级展示排序，维护管理用',
  attr_template_id VARCHAR(32)   DEFAULT NULL          COMMENT '属性模板 ID（规格/酒精度等按分类定义）',
  quality_grade    CHAR(1)       DEFAULT NULL          COMMENT '分类自身质量：覆盖度/未分类率评价 A/B/C/D',
  status           VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/DISABLED/MERGED',
  version          INT           NOT NULL DEFAULT 1    COMMENT '分类调整生成新版本，历史可追溯',
  PRIMARY KEY (category_id),
  KEY idx_parent (parent_id),
  KEY idx_path (category_path),
  KEY idx_external (external_code),
  KEY idx_leaf (is_leaf, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='N 级分类树：统计锚点 + 物化路径 + 维护属性';

-- ------------------------------------------------------------
-- 3. 分类来源映射表（分类治理核心）：把各来源的分类码归一到统一分类
--    解决：merged 独有 55 个卷烟细分码、01999999 未分类、跨文件分类冲突
--    规模小（几百行），只存映射规则不囤商品数据
-- ------------------------------------------------------------
CREATE TABLE mdm_category_map (
  map_id            BIGINT      NOT NULL AUTO_INCREMENT,
  source_system     VARCHAR(32) NOT NULL              COMMENT '来源系统：merged_csv/goods_csv/store_api',
  source_code       VARCHAR(16) NOT NULL              COMMENT '来源分类码（如 03000642 卷烟细分 / 01999999 未分类）',
  source_name       VARCHAR(64) DEFAULT NULL          COMMENT '来源分类名（merged 无名称则为空）',
  target_category_id VARCHAR(16) NOT NULL             COMMENT '治理后统一分类 ID，关联 mdm_category',
  map_type          VARCHAR(16) NOT NULL              COMMENT 'DIRECT 直映射/ROLLUP 上卷/FILLBACK 回填/ALIAS 别名/UNMAPPED 待处理',
  rule_code         VARCHAR(32) DEFAULT NULL          COMMENT 'CODE_MAP/NAME_MAP/AI_FILLBACK/MANUAL',
  confidence        DECIMAL(5,4) DEFAULT NULL         COMMENT '映射置信度',
  row_count         BIGINT      NOT NULL DEFAULT 0    COMMENT '该来源分类码覆盖商品数（治理统计）',
  status            VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/PENDING/REJECTED',
  PRIMARY KEY (map_id),
  UNIQUE KEY uk_src (source_system, source_code),
  KEY idx_target (target_category_id),
  KEY idx_type (map_type, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分类来源映射：各来源码归一到统一分类，保留原粒度';

-- 映射示例：
-- merged_csv 03000642 "寿百年" -> 卷烟末级(ROLLUP，保留细分粒度于 source_code)
-- goods_csv  01999999 "未分类" -> 待回填(UNMAPPED)，由 AI_FILLBACK 规则处理
-- goods_csv  03000001 "休闲零食" -> 休闲零食(DIRECT)

-- ------------------------------------------------------------
-- 4. 条码别名表：一物多码
-- ------------------------------------------------------------
CREATE TABLE mdm_barcode_alias (
  alias_id       BIGINT      NOT NULL AUTO_INCREMENT,
  alias_barcode  VARCHAR(32) NOT NULL                COMMENT '别名条码',
  master_barcode VARCHAR(32) NOT NULL                COMMENT '主条码，指向 mdm_goods.barcode',
  alias_type     VARCHAR(32) NOT NULL                COMMENT 'BIG_PACK 大包装/OLD_CODE 历史码（已删 EAN8_UPGRADE：EAN-8 不升位；X_CODE 随非数字码去除）',
  created_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (alias_id),
  UNIQUE KEY uk_alias (alias_barcode, alias_type),
  KEY idx_master (master_barcode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='条码别名：一物多码映射，主档仍唯一';

-- ------------------------------------------------------------
-- 5. 隔离区：同码异物、D 级、分类低置信待处理
-- ------------------------------------------------------------
CREATE TABLE dq_quarantine (
  quarantine_id BIGINT       NOT NULL AUTO_INCREMENT,
  batch_id      VARCHAR(32)  NOT NULL                COMMENT '治理批次',
  barcode       VARCHAR(32)  NOT NULL                COMMENT '条码（原值/规范值）',
  issue_type    VARCHAR(32)  NOT NULL                COMMENT 'SAME_CODE_DIFF_GOODS/EXTREME_PRICE/CATEGORY_LOW_CONF/LOW_CONFIDENCE',
  conflict_field VARCHAR(32) DEFAULT NULL            COMMENT '冲突字段（如 SORT_ID）',
  value_a       VARCHAR(256) DEFAULT NULL            COMMENT '候选值 A',
  value_b       VARCHAR(256) DEFAULT NULL            COMMENT '候选值 B',
  reason        VARCHAR(512) DEFAULT NULL            COMMENT '隔离原因简述',
  decision      VARCHAR(32)  DEFAULT NULL            COMMENT 'RECODED 重新赋码/ALIAS 别名/RELEASED 放行/REJECTED',
  owner         VARCHAR(64)  DEFAULT NULL            COMMENT '责任人',
  status        VARCHAR(16)  NOT NULL DEFAULT 'OPEN' COMMENT 'OPEN/TRACING/RESOLVED',
  sla_deadline  DATETIME     DEFAULT NULL            COMMENT '处理时限',
  resolution    VARCHAR(512) DEFAULT NULL            COMMENT '处理结果',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at   DATETIME     DEFAULT NULL,
  PRIMARY KEY (quarantine_id),
  KEY idx_barcode (barcode),
  KEY idx_type_status (issue_type, status),
  KEY idx_sla (status, sla_deadline)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='隔离区：同码异物/D 级/分类低置信，含 SLA 闭环';

-- ------------------------------------------------------------
-- 6. 治理批次：记录规则版本与输入输出统计，支撑重跑回滚
-- ------------------------------------------------------------
CREATE TABLE sys_gov_batch (
  batch_id       VARCHAR(32)  NOT NULL                COMMENT '批次号',
  batch_type     VARCHAR(16)  NOT NULL                COMMENT 'FULL 全量/REBUILD 重跑回滚/CATALOG_CLASSIFY 分类回填',
  rule_version   VARCHAR(32)  NOT NULL                COMMENT '版本组合：规则+模型+提示词+分类映射快照；回滚=用旧组合重跑覆盖',
  input_rows     BIGINT       NOT NULL DEFAULT 0      COMMENT '输入行数',
  valid_rows     BIGINT       NOT NULL DEFAULT 0      COMMENT '准入通过行数',
  excluded_rows  BIGINT       NOT NULL DEFAULT 0      COMMENT '丢弃的无效行数',
  output_rows    BIGINT       NOT NULL DEFAULT 0      COMMENT '产出主档数',
  quarantined_rows BIGINT     NOT NULL DEFAULT 0      COMMENT '隔离数',
  recategorized_rows BIGINT   NOT NULL DEFAULT 0      COMMENT '分类回填/映射商品数',
  auto_decided_rows BIGINT    NOT NULL DEFAULT 0      COMMENT '规则/众数自动判定数（KPI自动覆盖率分子）',
  ai_decided_rows  BIGINT     NOT NULL DEFAULT 0      COMMENT 'AI语义判定数（覆盖率分母=auto+ai；覆盖率=auto/(auto+ai)）',
  started_at     DATETIME     NOT NULL,
  finished_at    DATETIME     DEFAULT NULL,
  status         VARCHAR(16)  NOT NULL                COMMENT 'RUNNING/SUCCESS/FAILED/ROLLED_BACK',
  remark         VARCHAR(256) DEFAULT NULL,
  PRIMARY KEY (batch_id),
  KEY idx_status (status, started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='治理批次与统计：回滚靠旧规则版本重跑';

-- ------------------------------------------------------------
-- 7. 来源可信度：平票破局与分类冲突裁决的权重依据
-- ------------------------------------------------------------
CREATE TABLE sys_source_trust (
  source_code  VARCHAR(32)  NOT NULL                COMMENT '来源编码',
  source_name  VARCHAR(64)  NOT NULL                COMMENT '来源名称',
  trust_weight DECIMAL(5,4) NOT NULL DEFAULT 1.0000 COMMENT '可信度权重 0~1',
  enabled      TINYINT      NOT NULL DEFAULT 1       COMMENT '是否参与决策',
  remark       VARCHAR(256) DEFAULT NULL,
  PRIMARY KEY (source_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='来源可信度权重配置';

-- 默认权重（v3.2 补齐，使 TIE_C2_TRUST 可运行；业务可改配置无需改代码）
INSERT INTO sys_source_trust (source_code, source_name, trust_weight, remark) VALUES
  ('goods_csv','商品信息.csv', 0.9000, '字段更全，有分类名/单位/在销状态，默认优先'),
  ('merged_csv','merged.csv', 0.7000, '商品池更大但字段稀疏，创建时间被统一改写');

-- ============================================================
-- 零存储视图：统计分析口径（视图不占存储，符合"不囤数据"）
-- ============================================================

-- 视图1：商品-分类扁平宽表，统计直接 GROUP BY 任意层级
CREATE VIEW v_goods_category_stat AS
SELECT
  g.barcode, g.goods_name, g.category_id, g.category_path,
  g.category_source, g.outprice, g.inprice, g.status, g.quality_grade,
  c2.category_name AS leaf_name,
  c1.category_name AS parent_name,
  c1.category_id   AS parent_id,
  g.governance_batch
FROM mdm_goods g
LEFT JOIN mdm_category c2 ON g.category_id = c2.category_id
LEFT JOIN mdm_category c1 ON c2.parent_id  = c1.category_id;

-- 视图2：分类质量看板——各分类覆盖率、AI 回填量、未分类量
CREATE VIEW v_category_quality AS
SELECT
  c.category_id, c.category_name, c.category_level, c.quality_grade,
  COUNT(g.barcode) AS goods_count,
  SUM(CASE WHEN g.category_source = 'AI_FILLBACK' THEN 1 ELSE 0 END) AS ai_filled,
  SUM(CASE WHEN g.category_source = 'UNCLASSIFIED' THEN 1 ELSE 0 END) AS unclassified
FROM mdm_category c
LEFT JOIN mdm_goods g ON g.category_id = c.category_id
GROUP BY c.category_id, c.category_name, c.category_level, c.quality_grade;

-- ============================================================
-- 过程管理与目录管理 · 扩展表（专项方案 v1.0）
-- 说明：补齐"治理过程怎么被管控"与"数据资产怎么被登记理解"。
--       三张表合计 < 200 行（不到 1 MB），两个视图零存储；
--       不引入工作流引擎/元数据平台，不改 7 张成果表与七步加工逻辑。
--       详细设计见《方案一_过程管理与目录管理专项方案.html》。
-- ------------------------------------------------------------
-- 8. 治理步骤台账：批次内七步的状态、对账、重试与关卡判定
-- ------------------------------------------------------------
CREATE TABLE sys_gov_step (
  step_id       BIGINT       NOT NULL AUTO_INCREMENT,
  batch_id      VARCHAR(32)  NOT NULL                COMMENT '关联 sys_gov_batch.batch_id',
  step_no       TINYINT      NOT NULL                COMMENT '1..7：准入/分组/异物判别/投票/分类归一/众数落定/写主档',
  step_code     VARCHAR(32)  NOT NULL                COMMENT 'ADMIT/GROUP/DETECT/VOTE/CLASSIFY/MODE/WRITE',
  step_name     VARCHAR(64)  NOT NULL                COMMENT '步骤中文名',
  status        VARCHAR(16)  NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING/RUNNING/SUCCESS/FAILED/RETRIED/SKIPPED',
  input_rows    BIGINT       NOT NULL DEFAULT 0      COMMENT '该步输入行数（过程对账）',
  output_rows   BIGINT       NOT NULL DEFAULT 0      COMMENT '该步输出行数（过程对账）',
  error_code    VARCHAR(64)  DEFAULT NULL            COMMENT '失败机器码：DB_TIMEOUT/BARCODE_ALL_REJECTED 等',
  error_msg     VARCHAR(512) DEFAULT NULL            COMMENT '失败简述',
  retry_count   INT          NOT NULL DEFAULT 0      COMMENT '瞬时错误重试次数，上限 3',
  gate_code     VARCHAR(16)  DEFAULT NULL            COMMENT '关联质量关卡 G0/G1/G2/G3',
  gate_result   VARCHAR(16)  DEFAULT NULL            COMMENT 'PASS/FAIL/NA',
  started_at    DATETIME     DEFAULT NULL            COMMENT '开始时间',
  finished_at   DATETIME     DEFAULT NULL            COMMENT '结束时间',
  duration_sec  INT          DEFAULT NULL            COMMENT '耗时秒数，用于发现性能反常',
  operator      VARCHAR(64)  DEFAULT NULL            COMMENT '步骤责任人',
  PRIMARY KEY (step_id),
  UNIQUE KEY uk_batch_step (batch_id, step_no),
  KEY idx_status (status, step_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='治理步骤台账：批次内七步状态与行数对账';

-- ------------------------------------------------------------
-- 9. 数据资产目录：有哪些数据、在哪、谁负责、多久更新
-- ------------------------------------------------------------
CREATE TABLE sys_data_catalog (
  asset_id      VARCHAR(64)  NOT NULL                COMMENT '表名或视图名 = 主键',
  asset_name    VARCHAR(128) NOT NULL                COMMENT '资产中文名',
  asset_type    VARCHAR(16)  NOT NULL                COMMENT 'TABLE/VIEW/FILE',
  layer         VARCHAR(32)  NOT NULL                COMMENT 'SOURCE/RESULT/STAT/MANAGEMENT',
  grain         VARCHAR(128) DEFAULT NULL            COMMENT '数据粒度，如"一条码一条黄金记录"',
  primary_key   VARCHAR(64)  DEFAULT NULL            COMMENT '主键说明',
  purpose       VARCHAR(256) DEFAULT NULL            COMMENT '用途一句话，下游据此判断该不该用',
  source_system VARCHAR(64)  DEFAULT NULL            COMMENT '来源系统',
  update_freq   VARCHAR(32)  DEFAULT NULL            COMMENT 'FULL_BATCH 全量批次 / ON_DEMAND 按需',
  owner         VARCHAR(64)  DEFAULT NULL            COMMENT '资产责任人',
  sensitivity   VARCHAR(16)  DEFAULT NULL            COMMENT '公开/内部/敏感（价格类标内部）',
  retention     VARCHAR(64)  DEFAULT NULL            COMMENT '保留策略',
  version       INT          NOT NULL DEFAULT 1      COMMENT '目录自身版本，口径变更可追溯',
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (asset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据资产目录：数据资产的登记与发现';

-- ------------------------------------------------------------
-- 10. 字段数据字典：字段含义、取值域、字段级血缘
-- ------------------------------------------------------------
CREATE TABLE sys_field_dict (
  dict_id       BIGINT       NOT NULL AUTO_INCREMENT,
  table_name    VARCHAR(64)  NOT NULL                COMMENT '所属表/视图名，关联 sys_data_catalog.asset_id',
  column_name   VARCHAR(64)  NOT NULL                COMMENT '字段名',
  cn_name       VARCHAR(128) DEFAULT NULL            COMMENT '中文名',
  description   VARCHAR(512) DEFAULT NULL            COMMENT '口径说明，如 outprice=参考价非权威价',
  data_type     VARCHAR(64)  DEFAULT NULL            COMMENT '数据类型',
  nullable      TINYINT      DEFAULT NULL            COMMENT '是否可空',
  is_pk         TINYINT      NOT NULL DEFAULT 0      COMMENT '是否主键',
  value_domain  VARCHAR(256) DEFAULT NULL            COMMENT '枚举/取值范围，如 quality_grade=A/B/C/D',
  source_expr   VARCHAR(512) DEFAULT NULL            COMMENT '字段级血缘：来源字段或计算表达式',
  sensitivity   VARCHAR(16)  DEFAULT NULL            COMMENT '敏感级别',
  owner         VARCHAR(64)  DEFAULT NULL            COMMENT '字段责任人',
  version       INT          NOT NULL DEFAULT 1      COMMENT '口径版本',
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (dict_id),
  UNIQUE KEY uk_table_col (table_name, column_name),
  KEY idx_source (source_expr(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='字段数据字典：字段含义/取值域/字段级血缘';

-- ------------------------------------------------------------
-- 字段级血缘示例（写入 sys_field_dict.source_expr）
--   mdm_goods.goods_name  ← MODE(GODS_NAME: goods_csv+merged_csv; 平票 TIE_C1/C2/C3)
--   mdm_goods.outprice    ← MODE(OUTPRICE 剔除异常与倒挂; 平票 TIE_C2/C4_MEDIAN)  参考价
--   mdm_goods.category_id ← mdm_category_map.target_category_id (DIRECT/ROLLUP/FILLBACK)
--   mdm_goods.quality_grade ← QUALITY_SCORE(完整度/一致性/唯一性/及时性/有效性/可信度)
--   mdm_goods.decision_trace ← 每字段采纳值+来源，冲突字段附票数/规则/胜出来源（值级血缘指针）
-- 两级血缘配合：字段字典 source_expr 答"口径"，主档 decision_trace 答"这个值的决策"。
-- ------------------------------------------------------------

-- 视图3：过程看板——当前批次跑到哪步、哪步行数对不上、谁负责
CREATE VIEW v_gov_process AS
SELECT b.batch_id, b.batch_type, b.status AS batch_status,
       b.rule_version, b.input_rows, b.output_rows,
       s.step_no, s.step_name, s.status AS step_status,
       s.input_rows AS step_in, s.output_rows AS step_out,
       s.retry_count, s.gate_code, s.gate_result, s.error_code,
       s.operator, s.duration_sec
FROM sys_gov_batch b
LEFT JOIN sys_gov_step s ON s.batch_id = b.batch_id
ORDER BY b.started_at DESC, s.step_no;

-- 视图4：字段血缘查询——字段级血缘 + 资产归属 + 责任人
CREATE VIEW v_catalog_lineage AS
SELECT d.table_name, d.column_name, d.cn_name,
       d.source_expr AS field_lineage,
       c.source_system, c.update_freq, c.owner, c.sensitivity
FROM sys_field_dict d
JOIN sys_data_catalog c ON c.asset_id = d.table_name
WHERE d.source_expr IS NOT NULL
ORDER BY d.table_name, d.column_name;
-- ============================================================

-- ============================================================
-- 方案二启用表：扫码价格事件（治理阶段不建，校准阶段再建）
-- 说明：用户明确要求"未来用扫码成交价校准价格"，这是唯一需要新增的表。
--       只记校准必需字段，POS 交易明细仍在业务系统，不在主数据囤全量流水。
-- ------------------------------------------------------------
-- CREATE TABLE scan_price_event (
--   event_id    BIGINT       NOT NULL AUTO_INCREMENT,
--   barcode     VARCHAR(32)  NOT NULL              COMMENT '商品条码，关联 mdm_goods',
--   deal_price  DECIMAL(18,6) NOT NULL             COMMENT '扫码成交价（校准票）',
--   store_id    VARCHAR(32)  DEFAULT NULL          COMMENT '门店（可选）',
--   is_promo    TINYINT      NOT NULL DEFAULT 0    COMMENT '促销/会员价=1，不计入校准',
--   deal_time   DATETIME     NOT NULL              COMMENT '成交时间',
--   PRIMARY KEY (event_id),
--   KEY idx_barcode_time (barcode, deal_time),
--   KEY idx_promo (is_promo)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='扫码成交价事件：价格校准的唯一数据来源';
-- 校准逻辑：同一条码的成交价持续偏离主档价超阈值 → 按众数更新 outprice，
--           变更写主档 decision_trace（rule=CALIBRATION），并通知下游刷新。
-- ============================================================

-- ============================================================
-- 容量估算（全量，v3.2 按实测修正）
--   mdm_goods           446 万行  ≈ 3–4 GB（含索引）
--     其中 decision_trace 实测 399–504 字节/条，仅此一项 ≈ 1.8–2.3 GB
--   mdm_category         ≈ 200 行   可忽略
--   mdm_category_map     ≈ 400 行   可忽略
--   mdm_barcode_alias    ≈ 10 万行  ≈ 10 MB
--   dq_quarantine        ≈ 10 万行  ≈ 30 MB
--   sys_gov_batch / sys_source_trust  可忽略
--   过程管理与目录管理扩展：sys_gov_step 几十行 + sys_data_catalog ≈16 行
--     + sys_field_dict ≈120 行，三表合计 < 200 行（不到 1 MB），可忽略
--   视图：4 个，零存储
--   合计含索引 ≈ 4–5 GB（原估 1.5 GB 为低估约 2 倍）。单机 MySQL 仍可承载，无需分区/分库分表。
--
-- 分类治理要点：
--   1. 分类字典干净（0 冲突）→ mdm_category 直接沿用 goods 的 10 大类/144 末级
--   2. 未分类 27.2% → map 标 UNMAPPED，AI 回填后改 FILLBACK，低置信进隔离区
--   3. 体系不一致（merged 197 码 / goods 152 码 / 交集 142）→ 映射表归一，55 个卷烟细分码 ROLLUP 保留粒度
--   4. 统计分析 → category_path 物化路径 + v_goods_category_stat 视图，任意层级免复杂 JOIN
--   5. 分类质量 → mdm_category.quality_grade + v_category_quality 看板持续监控
--
-- 条码规范要点（v3.2，详见《商品条码规范 v1.0》）：
--   准入四关：纯数字 → 长度 8/13 → 校验位通过(GS1 mod-10) → 非 000 前缀
--   全量实测：去除 8.79 万行（校验错/补0/非数字/异常长度），保留 446.3 万
--   EAN-8 以原生 8 位为主键，不升位（00000 码中 95% 是店内码，升位会误判）
--   主键 barcode 允许 8 位或 13 位；别名表仅 BIG_PACK/OLD_CODE
--
-- 已删除（相对 v2.0）：
--   ods_goods_source / dwd_goods_standard / dws_field_vote / dws_conflict_case
--   mdm_price / mdm_goods_attribute / dq_quality_score / sys_audit_log
--   sys_dispatch_log（下游订正）：改用变更通知，不建订正表
--   scan_price_event：扫码校准阶段启用的唯一新增表，DDL 见上方"方案二启用表"段
-- ============================================================
