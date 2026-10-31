from lua_helpers import from_lua, load_module, to_lua


def years():
    return load_module("ap_years")


def freed(availability):
    runtime, module = years()
    table = to_lua(runtime, availability)
    module.free(table)
    return from_lua(table)


def test_a_model_available_from_a_year_becomes_available_from_the_start():
    result = freed({"yearFrom": 1980, "yearTo": 2010, "notifyWhenAvailable": True})
    assert result["yearFrom"] == 0 and result["yearTo"] == 0
    assert result["notifyWhenAvailable"] is False


def test_the_original_year_is_kept_where_the_mod_can_read_it_back():
    runtime, module = years()
    table = to_lua(runtime, {"yearFrom": 1980, "yearTo": 0})
    module.free(table)
    assert module.original(table) == 1980


def test_content_that_was_always_available_stays_at_zero():
    runtime, module = years()
    table = to_lua(runtime, {"yearFrom": 0, "yearTo": 1940})
    module.free(table)
    assert module.original(table) == 0 and from_lua(table)["yearTo"] == 0


def test_freeing_twice_does_not_lose_the_original_year():
    runtime, module = years()
    table = to_lua(runtime, {"yearFrom": 1960, "yearTo": 0})
    module.free(table)
    module.free(table)
    assert module.original(table) == 1960


def test_a_sort_key_that_is_not_a_year_is_never_read_as_one():
    runtime, module = years()
    table = to_lua(runtime, {"yearFrom": 1900, "notificationSortKey": 7})
    assert module.original(table) == 1900
    table = to_lua(runtime, {"yearFrom": 0, "notificationSortKey": 100000})
    assert module.original(table) == 0


def test_nothing_breaks_without_an_availability_table():
    runtime, module = years()
    module.free(None)
    assert module.original(None) is None


def test_freed_tells_whether_the_dates_were_removed_by_the_mod():
    runtime, module = years()
    plain = to_lua(runtime, {"yearFrom": 1980})
    assert module.freed(plain) is False
    module.free(plain)
    assert module.freed(plain) is True


def test_a_construction_has_its_templates_freed_too():
    runtime, module = years()
    table = to_lua(runtime, {
        "availability": {},
        "constructionTemplates": [
            {"availability": {"yearFrom": 1900, "yearTo": 1940}},
            {"availability": {"yearFrom": 1980, "yearTo": 0}},
        ],
    })
    module.free_construction(table)
    result = from_lua(table)
    assert [t["availability"]["yearFrom"] for t in result["constructionTemplates"]] == [0, 0]
    assert [t["availability"]["yearTo"] for t in result["constructionTemplates"]] == [0, 0]
    assert module.original(table["constructionTemplates"][2]["availability"]) == 1980
