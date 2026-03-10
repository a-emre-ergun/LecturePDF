from pathlib import Path
from gettext import translation

from kivy.lang import Observable

"""
This module handles internationalization for the application.
The Language observable implementation is based on Mathieu Virbel's 
repository: https://github.com/tito/kivy-gettext-example
"""


class Language(Observable):
    _observers = []
    _ugettext = None
    language = None

    def __init__(self, language: str = "en", language_path: str = "."):
        """language: locale name, language_path: data + po folder."""
        super().__init__()
        self.language = language
        self.language_path = language_path
        self.switch_language(language)

    def _(self, text: str) -> str:
        """Return translated text."""
        return self._ugettext(text)

    def fbind(self, name, func, args, **kwargs):
        """Function-bind remote calls."""
        if name == "_":
            self._observers.append((func, args, kwargs))
        else:
            return super().fbind(name, func, *args, **kwargs)

    def funbind(self, name, func, args, **kwargs):
        """Unregister Function-bound calls."""
        if name == "_":
            key = (func, args, kwargs)
            if key in self._observers:
                self._observers.remove(key)
        else:
            return super().funbind(name, func, *args, **kwargs)

    def switch_language(self, language: str):
        """Switch language and update all calls attached to this language."""
        locale_dir = Path(self.language_path) / "locale"

        try:
            locales = translation("base", locale_dir, languages=[language, ])
            self._ugettext = locales.gettext
        except Exception as e:
            print(f"Error ({language}): {e}")
            self._ugettext = lambda x: x

        self.language = language

        for func, largs, kwargs in self._observers:
            func(largs, None, None)
