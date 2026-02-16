from core.group_config import GroupConfig


def test_unknown_group_defaults_to_all(tmp_path, monkeypatch):
    monkeypatch.setattr(GroupConfig, "CONFIG_PATH", tmp_path / "group_config.json")

    allowed = GroupConfig.get_allowed_modules("unknown@g.us")

    assert allowed == ["all"]
    assert GroupConfig.is_module_allowed("unknown@g.us", "ED") is True


def test_register_and_whitelist_allow_deny(tmp_path, monkeypatch):
    monkeypatch.setattr(GroupConfig, "CONFIG_PATH", tmp_path / "group_config.json")

    GroupConfig.register_group("team@g.us", "Tim ED")
    ok = GroupConfig.set_allowed_modules("team@g.us", ["ED", "IPD"])

    assert ok is True
    assert GroupConfig.is_module_allowed("team@g.us", "ED") is True
    assert GroupConfig.is_module_allowed("team@g.us", "OPD") is False


def test_update_and_delete_group(tmp_path, monkeypatch):
    monkeypatch.setattr(GroupConfig, "CONFIG_PATH", tmp_path / "group_config.json")

    GroupConfig.register_group("ops@g.us", "Ops")
    updated = GroupConfig.update_group_name("ops@g.us", "Ops Updated")
    deleted = GroupConfig.delete_group("ops@g.us")

    assert updated is True
    assert deleted is True
    assert GroupConfig.get_config("ops@g.us") is None
