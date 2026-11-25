"""四条铁律单元测试：全部断言分支覆盖。"""
import pytest

from app.core.errors import BizError
from app.services import ironrules as ir


# ---------- 铁律① 查重三态 ----------
def test_check_duplicate_barcode_hit_returns_block(cur):
    # 用一个真实存在的条码
    cur.execute("SELECT barcode, goods_name FROM mdm_goods LIMIT 1")
    barcode, name = cur.fetchone()
    r = ir.check_duplicate(cur, barcode, name + "_同名不存在XYZ")
    assert r["barcode_exist"]["hit"] is True
    assert r["verdict"] == "BLOCK"


def test_check_duplicate_same_name_returns_warn(cur):
    # 造两个同名不同码（事务内，结束回滚）
    cur.execute("SELECT goods_name FROM mdm_goods WHERE goods_name IS NOT NULL LIMIT 1")
    name = cur.fetchone()[0]
    # 找一个该名字下已存在的条码，用另一个新条码查同名
    cur.execute("SELECT barcode FROM mdm_goods WHERE goods_name=%s LIMIT 1", (name,))
    row = cur.fetchone()
    if not row:
        pytest.skip("无可用同名样本")
    fake_barcode = "9999999999999"
    r = ir.check_duplicate(cur, fake_barcode, name)
    assert r["same_name"]["hit"] is True
    assert r["verdict"] == "WARN"


def test_check_duplicate_clean_returns_pass(cur):
    r = ir.check_duplicate(cur, "12345678", "绝无此商品名_测试唯一_99887766")
    assert r["verdict"] == "PASS"


def test_assert_can_create_block_raises_3001(cur):
    cur.execute("SELECT barcode FROM mdm_goods LIMIT 1")
    barcode = cur.fetchone()[0]
    with pytest.raises(BizError) as e:
        ir.assert_can_create(cur, barcode, "随便名字")
    assert e.value.code == 3001


def test_no_auto_merge_same_name(cur):
    """40.6% 同名多码基数下，同名不触发自动合并（verdict 不为 BLOCK）。"""
    cur.execute(
        "SELECT goods_name, count(*) c FROM mdm_goods "
        "GROUP BY goods_name HAVING count(*)>1 LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        pytest.skip("无同名多码样本")
    name = row[0]
    r = ir.check_duplicate(cur, "12345678", name)
    assert r["verdict"] != "BLOCK" or r["barcode_exist"]["hit"]


# ---------- 铁律② 条码不可改 ----------
def test_patch_whitelist_rejects_barcode():
    with pytest.raises(ValueError) as e:
        ir.assert_patch_whitelist({"barcode": "12345678"})
    assert "barcode" in str(e.value)


def test_patch_whitelist_rejects_unknown_field():
    with pytest.raises(ValueError):
        ir.assert_patch_whitelist({"hacker_field": 1})


def test_patch_whitelist_accepts_allowed():
    ir.assert_patch_whitelist({"goods_name": "新名", "outprice": 12.5, "version": 3})


# ---------- 铁律③ VOIDED 禁复用 ----------
def test_status_transition_legal_table():
    assert ir.can_transition("ACTIVE", "INACTIVE") is True
    assert ir.can_transition("INACTIVE", "ACTIVE") is True
    assert ir.can_transition("ACTIVE", "VOIDED") is True
    assert ir.can_transition("VOIDED", "ACTIVE") is False
    assert ir.can_transition("VOIDED", "INACTIVE") is False
    assert ir.can_transition("ACTIVE", "ACTIVE") is False


def test_register_voided_ban_writes_alias(cur):
    barcode = "777766661111"
    until = ir.register_voided_ban(cur, barcode, "tester", "MAN-TEST000000-tester")
    cur.execute(
        "SELECT alias_type, banned_until FROM mdm_barcode_alias WHERE alias_barcode=%s",
        (barcode,),
    )
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "VOIDED_BAN"
    assert row[1] == until


def test_assert_barcode_reusable_blocks_in_ban(cur):
    barcode = "777766662222"
    ir.register_voided_ban(cur, barcode, "tester", "MAN-TEST000000-tester")
    with pytest.raises(BizError) as e:
        ir.assert_barcode_reusable(cur, barcode)
    assert e.value.code == 3003


def test_assert_status_transition_voided_is_final(cur):
    # 用事务把一条样本置 VOIDED（结束回滚）
    cur.execute("SELECT barcode FROM mdm_goods LIMIT 1")
    barcode = cur.fetchone()[0]
    cur.execute("UPDATE mdm_goods SET status='VOIDED' WHERE barcode=%s", (barcode,))
    with pytest.raises(BizError) as e:
        ir.assert_status_transition(cur, barcode, "ACTIVE")
    assert e.value.code == 3007


# ---------- 乐观锁 ----------
def test_assert_version_conflict(cur):
    cur.execute("SELECT barcode, version FROM mdm_goods LIMIT 1")
    barcode, ver = cur.fetchone()
    ir.assert_version(cur, barcode, ver)  # 正确版本通过
    with pytest.raises(BizError) as e:
        ir.assert_version(cur, barcode, ver + 999)
    assert e.value.code == 3009


# ---------- 条码格式 / 书号识别 ----------
def test_barcode_format():
    assert ir.valid_barcode_format("12345678") is True
    assert ir.valid_barcode_format("1234567890123") is True
    assert ir.valid_barcode_format("123") is False
    assert ir.valid_barcode_format("1234567a") is False


def test_isbn_detection():
    assert ir.is_isbn("9781234567890") is True
    assert ir.is_isbn("9791234567890") is True
    assert ir.is_isbn("6931234567890") is False
