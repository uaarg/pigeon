from PyQt5 import QtCore

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

    def __init__(self,
                 *args,
                 settings_data={},
                 fields_to_display=True,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.fields_to_display = fields_to_display

        self.setSettings(settings_data)

        self.dataEdited.connect(
            lambda: self.settings_save_requested.emit(self.getSettings()))

    def _title(self):
        return "Settings:"

    def setSettings(self, settings_data):
        if self.fields_to_display is True:
            fields_to_display = sorted(settings_data.keys())
        else:
            fields_to_display = self.fields_to_display
        data = [(field_name, settings_data[field_name])
                for field_name in fields_to_display]
        self.setData(data)

    def getSettings(self):
        data = self.getData()
        settings = {row[0]: row[1] for row in data}
        return settings
