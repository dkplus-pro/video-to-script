from vlog_script_generator.output.markdown_writer import SCRIPT_COLUMNS, rows_to_markdown


def test_rows_to_markdown_escapes_pipes():
    row = {col: "" for col in SCRIPT_COLUMNS}
    row.update({"序号": "1", "脚本内容": "a|b"})
    markdown = rows_to_markdown([row])
    assert "\\|" in markdown
    assert markdown.count("\n") == 3

