from io import StringIO
from typing import Dict
from uuid import uuid4

import pytest

from alert_msgs.components import (
    ContentType,
    FontSize,
    Map,
    Table,
    Text,
    render_components_html,
    render_components_md,
)

str_dict = {str(uuid4()): str(uuid4()) for _ in range(2)}


def text_has_content(text: str, content: Dict[str, str] = str_dict) -> bool:
    return all(k in text and v in text for k, v in content.items())


@pytest.mark.parametrize("size", list(FontSize.__members__.values()))
@pytest.mark.parametrize("content_type", list(ContentType.__members__.values()))
def test_text_render(size, content_type):
    content = str(uuid4())
    o = Text(content, content_type, size)
    assert content in o.html().render()
    assert content in o.classic_md()
    assert content in o.slack_md()


def test_map_render():
    o = Map(str_dict)
    assert text_has_content(o.html().render())
    assert text_has_content(o.classic_md())
    assert text_has_content(o.slack_md())


@pytest.mark.parametrize("caption", [None, str(uuid4())])
@pytest.mark.parametrize("meta", [None, str_dict])
@pytest.mark.parametrize("attach_rows", [False, True])
def test_table_render(caption, meta, attach_rows):
    rows = [{k: v * i for k, v in str_dict.items()} for i in range(1, 3)]

    def text_has_rows(text):
        return all(text_has_content(text, r) for r in rows)

    o = Table(body=rows, title=caption, header=meta)

    if attach_rows:
        filename, file = o.attach_rows_as_file()
        assert isinstance(filename, str)
        assert isinstance(file, StringIO)
        file_content = file.read()
        assert text_has_rows(file_content)
        assert not text_has_rows(o.html().render())
        assert not text_has_rows(o.classic_md())
        assert not text_has_rows(o.slack_md())
    else:
        assert text_has_rows(o.html().render())
        assert text_has_rows(o.classic_md())
        assert text_has_rows(o.slack_md())

    if caption is not None:
        assert caption in o.html().render()
        assert caption in o.classic_md()
        assert caption in o.slack_md()

    if not attach_rows and meta is not None:
        assert text_has_content(o.html().render())
        assert text_has_content(o.classic_md())
        assert text_has_content(o.slack_md())


def test_render_components_html(components):
    html = render_components_html(components)
    assert isinstance(html, str)


@pytest.mark.parametrize("slack_format", [False, True])
def test_render_components_md(components, slack_format):
    md = render_components_md(components, slack_format)
    assert isinstance(md, str)
