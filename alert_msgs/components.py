import csv
import pickle
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum, auto
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from dominate import document
from dominate import tags as d
from premailer import transform
from prettytable import PrettyTable
from xxhash import xxh32

from .utils import as_code_block


# TODO List component.
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


def level_css_color(level: ContentType) -> str:
    """Get an appropriate CSS color for a given `ContentType`."""
    # TODO add this to settings.
    colors = {
        ContentType.INFO: "black",
        ContentType.WARNING: "#ffca28;",
        ContentType.ERROR: "#C34A2C",
        ContentType.IMPORTANT: "#1967d3",
    }
    return colors.get(level, colors[ContentType.INFO])


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
        value: str,
        level: ContentType = ContentType.INFO,
        font_size: FontSize = FontSize.MEDIUM,
    ):
        """
        Args:
            content (str): The text that should be displayed in the component.
            level (ContentType, optional): Type of text. Defaults to ContentType.INFO.
            font_size (FontSize, optional): Size of font. Defaults to FontSize.MEDIUM.
        """
        self.value = str(value)
        self.level = level
        self.font_size = font_size

    def html(self) -> d.html_tag:
        tag = self._content_tags[self.level]
        return tag(
            self.value,
            style=f"font-size:{font_size_css(self.font_size)};color:{level_css_color(self.level)};",
        )

    def classic_md(self) -> str:
        if self.font_size is FontSize.SMALL:
            return self.value
        if self.font_size is FontSize.MEDIUM:
            return f"## {self.value}"
        if self.font_size is FontSize.LARGE:
            return f"# {self.value}"

    def slack_md(self) -> str:
        if self.level in (ContentType.IMPORTANT, ContentType.ERROR):
            return f"*{self.value}*"
        return self.value


class Map(MsgComp):
    """A component that displays formatted key/value pairs."""

    def __init__(self, data: Dict[str, Any], inline: bool = False):
        """
        Args:
            data (Dict[str, Any]): The key/value pairs that should be displayed.
            inline (bool, optional): Whether to put each field/value pair on its own line. Defaults to False.
        """
        self.data = data
        # TODO automatic inlining based on text lengths.
        self.inline = inline

    def html(self) -> d.html_tag:
        kv_tag = d.span("\t") if self.inline else d.div
        with (container := d.div()):
            for k, v in self.data.items():
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
        for k, v in self.data.items():
            rows.append(f"|**{k}:**|{v}|")
        rows.append("|||")
        join_method = "\t" if self.inline else "\n"
        return join_method.join(rows)

    def slack_md(self) -> str:
        join_method = "\t" if self.inline else "\n"
        return join_method.join([f"*{k}:* {v}" for k, v in self.data.items()])


class Table(MsgComp):
    """A component that displays tabular data."""

    def __init__(
        self,
        rows: Sequence[Dict[str, Any]],
        title: Optional[str] = None,
        columns: Optional[Sequence[str]] = None,
    ):
        """
        Args:
            rows (Sequence[Dict[str, Any]]): Iterable of row dicts (column: value).
            title (Optional[str], optional): A title to display above the table body. Defaults to None.
            columns (Optional[Sequence[str]], optional): A list of column names. Defaults to None (will be inferred from body rows).
        """
        self.rows = [{k: str(v) for k, v in row.items()} for row in rows]
        self.title = (
            Text(title, ContentType.IMPORTANT, FontSize.LARGE) if title else None
        )
        self.columns = (
            list({c for row in self.rows for c in row.keys()})
            if columns is None
            else columns
        )
        self._attachment: Map = None

    def attach_rows_as_file(self) -> Tuple[str, StringIO]:
        """Create a CSV file containing the table rows.

        Returns:
            Tuple[str, StringIO]: Name of file and file object.
        """
        stem = self.title.value[:50].replace(" ", "_") if self.title else "table"
        rows_id = xxh32(pickle.dumps(self.rows)).hexdigest()
        filename = f"{stem}_{rows_id}.csv"
        file = StringIO()
        writer = csv.DictWriter(file, fieldnames=self.columns)
        writer.writeheader()
        writer.writerows(self.rows)
        file.seek(0)
        self._attachment = Map({"Attachment": filename})
        # Don't render rows now that they're attached in a file.
        self.rows = None
        return filename, file

    def html(self):
        with (container := d.div(style="border:1px solid black;")):
            if self.title:
                self.title.html()
            if self._attachment:
                self._attachment.html()
            if self.rows:
                with d.div():
                    with d.table():
                        with d.tr():
                            for column in self.columns:
                                d.th(column)
                        for row in self.rows:
                            with d.tr():
                                for column in self.columns:
                                    d.td(row.get(column, ""))
        return container

    def classic_md(self) -> str:
        data = []
        if self.title:
            data.append(self.title.classic_md())
        if self._attachment:
            data.append(self._attachment.classic_md())
        if self.rows:
            table_rows = [
                self.columns,
                [":----:" for _ in range(len(self.columns))],
            ] + [[row[col] for col in self.columns] for row in self.rows]
            data.append("\n".join(["|".join(row) for row in table_rows]))
        return "\n\n".join(data).strip()

    def slack_md(self, float_format: str = ".3") -> str:
        if not self.rows:
            return ""
        columns = defaultdict(list)
        for row in self.rows:
            for k, v in row.items():
                columns[k].append(v)
        # Slack can't render very many rows in a single table.
        max_rows = 15
        table_slices = defaultdict(PrettyTable)
        for column, values in columns.items():
            for i in range(0, len(values), max_rows):
                table = table_slices[i]
                table.add_column(column, values[i : i + max_rows])
        data = []
        if self.title:
            data.append(table_slices.pop(0).get_string(title=self.title.value))
        for table in table_slices.values():
            if float_format:
                table.float_format = float_format
            data.append(table.get_string())
        data = [as_code_block(d) for d in data]
        if self._attachment:
            data.append(self._attachment.slack_md())
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
    if isinstance(components, (MsgComp, str)):
        components = [components]
    return [Text(comp) if isinstance(comp, str) else comp for comp in components]
