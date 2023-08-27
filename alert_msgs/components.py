import csv
import pickle
from abc import ABC, abstractmethod
from enum import Enum, auto
from hashlib import md5
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from dominate import document
from dominate import tags as d
from premailer import transform

from .settings import alert_settings


class MsgComp(ABC):
    """A structured component of a message."""

    @abstractmethod
    def html(self) -> d.html_tag:
        """Render the component's content as a `dominate` HTML element.

        Returns:
            d.html_tag: The HTML element with text.
        """
        pass

    def md(self, slack_format: bool) -> str:
        """Render the component's content as Markdown.

        Args:
            slack_format (bool): Use Slack's subset of Markdown features.

        Returns:
            str: The rendered Markdown.
        """
        if slack_format:
            return self.slack_md()
        return self.classic_md()

    @abstractmethod
    def classic_md(self) -> str:
        """Render the component's content as traditional Markdown.

        Returns:
            str: The rendered Markdown.
        """
        pass

    @abstractmethod
    def slack_md(self) -> str:
        """Render the component's content using Slack's subset of Markdown features.

        Returns:
            str: The rendered Markdown.
        """
        pass


class FontSize(Enum):
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()


class ContentType(Enum):
    IMPORTANT = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


def content_type_css_color(content_type: ContentType) -> str:
    """Get an appropriate CSS color for a given `ContentType`."""
    # TODO add this to settings.
    colors = {
        ContentType.INFO: "black",
        ContentType.WARNING: "#ffca28;",
        ContentType.ERROR: "#C34A2C",
        ContentType.IMPORTANT: "#1967d3",
    }
    return colors.get(content_type, colors[ContentType.INFO])


def font_size_css(font_size: FontSize) -> str:
    """Get an appropriate CSS font size for a given `FontSize`."""
    fonts = {
        FontSize.SMALL: "16px",
        FontSize.MEDIUM: "18px",
        FontSize.LARGE: "20px",
    }
    return fonts.get(font_size, fonts[FontSize.MEDIUM])


class Text(MsgComp):
    """A component that displays formatted text."""

    _content_tags = {
        ContentType.INFO: d.div,
        ContentType.WARNING: d.p,
        ContentType.ERROR: d.h2,
        ContentType.IMPORTANT: d.h1,
    }

    def __init__(
        self,
        content: str,
        content_type: ContentType = ContentType.INFO,
        font_size: FontSize = FontSize.MEDIUM,
    ):
        """
        Args:
            content (str): The text that should be displayed in the component.
            content_type (ContentType, optional): Type of text. Defaults to ContentType.INFO.
            font_size (FontSize, optional): Size of font. Defaults to FontSize.MEDIUM.
        """
        self.content = str(content)
        self.content_type = content_type
        self.font_size = font_size

    def html(self) -> d.html_tag:
        tag = self._content_tags[self.content_type]
        return tag(
            self.content,
            style=f"font-size:{font_size_css(self.font_size)};color:{content_type_css_color(self.content_type)};",
        )

    def classic_md(self) -> str:
        if self.font_size is FontSize.SMALL:
            return self.content
        if self.font_size is FontSize.MEDIUM:
            return f"## {self.content}"
        if self.font_size is FontSize.LARGE:
            return f"# {self.content}"

    def slack_md(self) -> str:
        if self.content_type in (ContentType.IMPORTANT, ContentType.ERROR):
            return f"*{self.content}*"
        return self.content


class Map(MsgComp):
    """A component that displays formatted key/value pairs."""

    def __init__(self, content: Dict[str, Any], inline: Optional[bool] = None):
        """
        Args:
            content (Dict[str, Any]): The key/value pairs that should be displayed.
            inline (Optional[bool], optional): Whether to put each field/value pair on its own line. Defaults to None.
        """
        self.content = content
        # TODO automatic inlining based on text lengths.
        self.inline = inline if inline is not None else alert_settings.inline_kv

    def html(self) -> d.html_tag:
        kv_tag = d.span("\t") if self.inline else d.div
        with (container := d.div()):
            for k, v in self.content.items():
                kv_tag(
                    d.span(
                        d.b(
                            Text(
                                f"{k}: ",
                                ContentType.IMPORTANT,
                                FontSize.LARGE,
                            ).html()
                        ),
                        Text(v, font_size=FontSize.LARGE).html(),
                    )
                )
        return container

    def classic_md(self) -> str:
        rows = ["|||", "|---:|:---|"]
        for k, v in self.content.items():
            rows.append(f"|**{k}:**|{v}|")
        rows.append("|||")
        join_method = "\t" if self.inline else "\n"
        return join_method.join(rows)

    def slack_md(self) -> str:
        join_method = "\t" if self.inline else "\n"
        return join_method.join([f"*{k}:* {v}" for k, v in self.content.items()])


class Table(MsgComp):
    """A component that displays tabular data."""

    def __init__(
        self,
        body: Sequence[Dict[str, Any]],
        title: Optional[str] = None,
        header: Optional[Sequence[str]] = None,
    ):
        """
        Args:
            body (Sequence[Dict[str, Any]]): Iterable of row dicts (column: value).
            title (Optional[str], optional): A title to display above the table body. Defaults to None.
            header (Optional[Sequence[str]], optional): A list of column names. Defaults to None (will be inferred from body rows).
        """
        self.body = [{k: str(v) for k, v in row.items()} for row in body]
        self.title = (
            Text(title, ContentType.IMPORTANT, FontSize.LARGE) if title else None
        )
        self.header = (
            list({c for row in self.body for c in row.keys()})
            if header is None
            else header
        )
        self._attachment: Map = None

    def attach_rows_as_file(self) -> Tuple[str, StringIO]:
        """Create a CSV file containing the table rows.

        Returns:
            Tuple[str, StringIO]: Name of file and file object.
        """
        stem = self.title.body[:50].replace(" ", "_") if self.title else "table"
        body_id = md5(pickle.dumps(self.body)).hexdigest()
        filename = f"{stem}_{body_id}.csv"
        file = StringIO()
        writer = csv.DictWriter(file, fieldnames=self.header)
        writer.writeheader()
        writer.writerows(self.body)
        file.seek(0)
        self._attachment = Map({"Attachment": filename})
        # Don't render rows now that they're attached in a file.
        self.body = None
        return filename, file

    def html(self):
        with (container := d.div(style="border:1px solid black;")):
            if self.title:
                self.title.html()
            if self._attachment:
                self._attachment.html()
            if self.body:
                with d.div():
                    with d.table():
                        with d.tr():
                            for column in self.header:
                                d.th(column)
                        for row in self.body:
                            with d.tr():
                                for column in self.header:
                                    d.td(row.get(column, ""))
        return container

    def classic_md(self) -> str:
        data = []
        if self.title:
            data.append(self.title.classic_md())
        if self._attachment:
            data.append(self._attachment.classic_md())
        if self.body:
            table_rows = [self.header, [":----:" for _ in range(len(self.header))]] + [
                [row[col] for col in self.header] for row in self.body
            ]
            data.append("\n".join(["|".join(row) for row in table_rows]))
        return "\n\n".join(data).strip()

    def slack_md(self) -> str:
        data = []
        if self.title:
            data.append(self.title.slack_md())
        if self._attachment:
            data.append(self._attachment.slack_md())
        if self.body:
            rows = [dict(zip(self.header, self.header))] + self.body
            # column width is length of longest string + a space of padding on both sides.
            columns_widths = {
                c: max(len(row[c]) for row in rows) + 2 for c in self.header
            }
            data.append(
                "\n".join(
                    [
                        "|".join(
                            [
                                f"{{: ^{columns_widths[col]}}}".format(row[col])
                                for col in self.header
                            ]
                        )
                        for row in rows
                    ]
                )
            )
        return "\n\n".join(data).strip()


class LineBreak(MsgComp):
    """A line beak (to be inserted between components)."""

    def __init__(self, n_break: int = 1) -> None:
        self.n_break = n_break

    def html(self) -> d.html_tag:
        with (container := d.div()):
            for _ in range(self.n_break):
                d.br()
        return container

    def classic_md(self) -> str:
        return "".join(["\n" for _ in range(self.n_break)])

    def slack_md(self) -> str:
        return self.classic_md()


def render_components_html(components: Sequence[MsgComp]) -> str:
    """Compile components into email-safe HTML.

    Args:
        components (Sequence[MsgComp]): The components to include in the HTML.

    Returns:
        str: The generated HTML.
    """
    components = _components_list(components)
    doc = document()
    with doc.head:
        d.style("body {text-align:center;}")
    # check size of tables to determine how best to process.
    if any(isinstance(c, Table) for c in components):
        with doc.head:
            d.style(Path(__file__).parent.joinpath("styles", "table.css").read_text())
    with doc:
        for c in components:
            d.div(c.html())
            d.br()

    return transform(doc.render())


def render_components_md(components: Sequence[MsgComp], slack_format: bool) -> str:
    """Compile components to Markdown.

    Args:
        components (Sequence[MsgComp]): The components to include in the Markdown.
        slack_format (bool): Render the components using Slack's subset of Markdown features.

    Returns:
        str: The generated Markdown.
    """
    components = _components_list(components)
    return "\n\n".join([c.md(slack_format) for c in components]).strip()


def _components_list(components: Sequence[MsgComp]) -> List[MsgComp]:
    if isinstance(components, MsgComp):
        components = [components]
    return [Text(comp) if isinstance(comp, str) else comp for comp in components]
