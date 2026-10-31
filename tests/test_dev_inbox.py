import os

import dev_inbox


def make(tmp_path, account: str, mtime: int):
    local = tmp_path / "userdata" / account / "3493540" / "local"
    folder = local / "towns_industries"
    folder.mkdir(parents=True)
    os.utime(local, (mtime, mtime))
    return folder


def test_the_exchange_folder_of_the_most_recently_used_steam_account_is_found(tmp_path):
    make(tmp_path, "111", 1_000)
    newest = make(tmp_path, "222", 2_000)
    assert dev_inbox.find_exchange_dir(tmp_path) == newest


def test_an_explicit_override_wins(tmp_path):
    make(tmp_path, "111", 1_000)
    assert dev_inbox.find_exchange_dir(tmp_path, override=str(tmp_path / "mine")) == tmp_path / "mine"


def test_no_steam_account_gives_no_folder(tmp_path):
    assert dev_inbox.find_exchange_dir(tmp_path) is None
