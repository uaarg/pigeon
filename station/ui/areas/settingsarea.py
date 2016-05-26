from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from ..commonwidgets import EditableBaseListForm, BoldQLabel

class SettingsArea(QtWidgets.QWidget):
    """
    Provides a simple form for displaying and editing settings.
    The settings should be provided in settings_data, a dictionary of
    strings and bools (only supported types at the moment). The
    dictionary keys should be strings and as the setting label.
    """

    settings_save_requested = QtCore.pyqtSignal(dict)
    settings_load_requested = QtCore.pyqtSignal()


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout()

        self.title = BoldQLabel(self)
        self.title.setText(translate("SettingsArea", "Settings:"))
        self.layout.addWidget(self.title)

        self.edit_form = EditableBaseListForm(self)
        self.layout.addWidget(self.edit_form)

        self.setLayout(self.layout)

        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        self.load_button = QtWidgets.QPushButton(translate("SettingsArea", "Load"), self)
        self.save_button = QtWidgets.QPushButton(translate("SettingsArea", "Save"), self)
        self.buttons_layout.addWidget(self.load_button)
        self.buttons_layout.addWidget(self.save_button)

        self.load_button.clicked.connect(self.settings_load_requested)
        self.save_button.clicked.connect(lambda: self.settings_save_requested.emit(self.getSettings()))


    def setSettings(self, settings_data):
        # Sorting for consistency in the UI between sessions
        sorted_settings_data = sorted(settings_data.items())
        data = [(field_name, field_value) for field_name, field_value in sorted_settings_data]
            # Converting the dictinary to a list of tuples because this is what the EditableBaseListForm needs
        self.edit_form.setData(data)

    def getSettings(self):
        data = self.edit_form.getData()
        settings_data = {row[0]:row[1] for row in data}
        return settings_data
