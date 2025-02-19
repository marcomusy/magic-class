""" Defines classes and functions for working with Qt's rich text system.
"""
# Mostly copied from:
# https://github.com/jupyter/qtconsole/blob/master/qtconsole/rich_text.py
# Typing, docstring, and some code changes are made.

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import re

from qtpy import QtWidgets as QtW

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# A regular expression for an HTML paragraph with no content.
EMPTY_P_RE = re.compile(r"<p[^/>]*>\s*</p>")

# A regular expression for matching images in rich text HTML.
# Note that this is overly restrictive, but Qt's output is predictable...
IMG_RE = re.compile(r'<img src="(?P<name>[\d]+)" />')

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class HtmlExporter:
    """A stateful HTML exporter for a Q(Plain)TextEdit.

    This class is designed for convenient user interaction.
    """

    def __init__(self, control: QtW.QPlainTextEdit | QtW.QTextEdit):
        """Creates an HtmlExporter for the given Q(Plain)TextEdit."""
        assert isinstance(control, (QtW.QPlainTextEdit, QtW.QTextEdit))
        self.control = control
        self.filename = None

    def export(self):
        """Displays a dialog for exporting HTML generated by Qt's rich text
        system.

        Returns
        -------
        The name of the file that was saved, or None if no file was saved.
        """
        parent = self.control.window()
        dialog = QtW.QFileDialog(parent, "Save as...")
        dialog.setAcceptMode(QtW.QFileDialog.AcceptMode.AcceptSave)
        filters = [
            "HTML with PNG figures (*.html *.htm)",
            "XHTML with inline SVG figures (*.xhtml *.xml)",
        ]
        dialog.setNameFilters(filters)
        if self.filename:
            dialog.selectFile(self.filename)
            root, ext = os.path.splitext(self.filename)
            if ext.lower() in (".xml", ".xhtml"):
                dialog.selectNameFilter(filters[-1])

        if dialog.exec_():
            self.filename = dialog.selectedFiles()[0]
            choice = dialog.selectedNameFilter()
            html = self.control.document().toHtml()

            # Configure the exporter.
            if choice.startswith("XHTML"):
                exporter = export_xhtml
            else:
                exporter = export_html

            # Perform the export!
            try:
                return exporter(html, self.filename, self.image_tag)
            except Exception as e:
                msg = f"Error exporting HTML to {self.filename}\n{e}"
                QtW.QMessageBox.warning(
                    parent,
                    "Error",
                    msg,
                    QtW.QMessageBox.StandardButton.Ok,
                    QtW.QMessageBox.StandardButton.Ok,
                )

        return None

    def _get_image(self, name):
        from qtpy import QtCore, QtGui

        document = self.control.document()
        image = document.resource(
            QtGui.QTextDocument.ResourceType.ImageResource,
            QtCore.QUrl(name),
        )
        return image

    def image_tag(self, match, path, format: str):
        from qtpy import QtCore, QtGui

        try:
            document = self.control.document()
            image = document.resource(
                QtGui.QTextDocument.ResourceType.ImageResource,
                QtCore.QUrl(match.group("name")),
            )
        except KeyError:
            return "<b>Couldn't find image %s</b>" % match.group("name")

        ba = QtCore.QByteArray()
        buffer_ = QtCore.QBuffer(ba)
        buffer_.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer_, format.upper())
        buffer_.close()
        return '<img src="data:image/{};base64,\n{}\n" />'.format(
            format, re.sub(r"(.{60})", r"\1\n", str(ba.toBase64().data().decode()))
        )


# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def export_html(html: str, filename: str, image_tag, inline=True):
    """Export the contents of the ConsoleWidget as HTML.

    Parameters
    ----------
    html : unicode,
        A Python unicode string containing the Qt HTML to export.

    filename : str
        The file to be saved.

    inline : bool, optional [default True]
        If True, include images as inline PNGs.  Otherwise, include them as
        links to external PNG files, mimicking web browsers' "Web Page,
        Complete" behavior.
    """

    if inline:
        path = None
    else:
        root, ext = os.path.splitext(filename)
        path = root + "_files"
        if os.path.isfile(path):
            raise OSError("%s exists, but is not a directory." % path)

    with open(filename, "w", encoding="utf-8") as f:
        html = fix_html(html)
        f.write(IMG_RE.sub(lambda x: image_tag(x, path=path, format="png"), html))


def export_xhtml(html: str, filename: str, image_tag):
    """Export the contents of the ConsoleWidget as XHTML with inline SVGs.

    Parameters
    ----------
    html : unicode,
        A Python unicode string containing the Qt HTML to export.

    filename : str
        The file to be saved.

    image_tag : callable, optional (default None)
        Used to convert images. See ``default_image_tag()`` for information.
    """
    with open(filename, "w", encoding="utf-8") as f:
        # Hack to make xhtml header -- note that we are not doing any check for
        # valid XML.
        offset = html.find("<html>")
        assert offset > -1, "Invalid HTML string: no <html> tag."
        html = '<html xmlns="http://www.w3.org/1999/xhtml">\n' + html[offset + 6 :]

        html = fix_html(html)
        f.write(IMG_RE.sub(lambda x: image_tag(x, path=None, format="svg"), html))


def fix_html(html: str):
    """Transforms a Qt-generated HTML string into a standards-compliant one.

    Parameters
    ----------
    html : unicode,
        A Python unicode string containing the Qt HTML.
    """
    # A UTF-8 declaration is needed for proper rendering of some characters
    # (e.g., indented commands) when viewing exported HTML on a local system
    # (i.e., without seeing an encoding declaration in an HTTP header).
    # C.f. http://www.w3.org/International/O-charset for details.
    offset = html.find("<head>")
    if offset > -1:
        html = (
            html[: offset + 6]
            + '\n<meta http-equiv="Content-Type" '
            + 'content="text/html; charset=utf-8" />\n'
            + html[offset + 6 :]
        )

    # Replace empty paragraphs tags with line breaks.
    html = re.sub(EMPTY_P_RE, "<br/>", html)

    return html
