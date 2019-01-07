from typing import Optional

from AppKit import NSAlert
from AppKit import NSApp
from rumps.compat import string_types
from rumps.compat import text_type
from rumps.rumps import Response
from rumps.rumps import _nsimage_from_file
from rumps.rumps import _require_string
from rumps.rumps import _require_string_or_none


class Alert:
    def __init__(self, message: str = '', title: str = '', ok: Optional[str] = None, cancel: Optional[str] = None):
        message = text_type(message)
        title = text_type(title)

        self._cancel = bool(cancel)
        self._icon = None

        _require_string_or_none(ok)
        if not isinstance(cancel, string_types):
            cancel = 'Cancel' if cancel else None

        self._alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
            title, ok, cancel, None, message)
        self._alert.setAlertStyle_(0)

        NSApp.activateIgnoringOtherApps_(True)

    @property
    def title(self) -> str:
        return self._alert.messageText()

    @title.setter
    def title(self, new_title: str):
        self._alert.setMessageText_(text_type(new_title))

    @property
    def message(self) -> str:
        return self._alert.informativeText()

    @message.setter
    def message(self, new_message: str):
        self._alert.setInformativeText_(text_type(new_message))

    @property
    def icon(self) -> str:
        return self._icon

    @icon.setter
    def icon(self, icon_path: str):
        new_icon = _nsimage_from_file(icon_path) if icon_path is not None else None
        self._icon = icon_path
        self._alert.setIcon_(new_icon)

    def add_button(self, name: str):
        _require_string(name)
        self._alert.addButtonWithTitle_(name)

    def add_buttons(self, iterable=None, *args):
        if iterable is None:
            return

        if isinstance(iterable, string_types):
            self.add_button(iterable)
        else:
            for button in iterable:
                self.add_button(button)

        for arg in args:
            self.add_button(arg)

    def run(self) -> Response:
        clicked = self._alert.runModal() % 999

        if clicked > 2 and self._cancel:
            clicked -= 1

        return Response(clicked, None)
