from PyQt6 import QtCore

translate = QtCore.QCoreApplication.translate

from ..commonwidgets import EditableBaseListForm


class SettingsArea(EditableBaseListForm):
    """
    Provides a simple form for displaying and editing common settings.
    The settings should be provided in settings_data, a dictionary of
    strings and bools (only supported types at the moment). The
    dictionary keys should be strings and as the setting label.
    """

    settings_save_requested = QtCore.pyqtSignal(dict)

    def __init__(self, *args, fields_to_display=True, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields_to_display = fields_to_display

        self.dataEdited.connect(
            lambda: self.settings_save_requested.emit(self.getSettings()))
