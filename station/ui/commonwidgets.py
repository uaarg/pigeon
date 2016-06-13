from PyQt5 import QtCore, QtWidgets
translate = QtCore.QCoreApplication.translate

class BoldQLabel(QtWidgets.QLabel):
    """
    Bolding defined in the stylesheet.
    """

class EditableBaseListForm(QtWidgets.QWidget):
    dataEdited = QtCore.pyqtSignal(list)

    def __init__(self, *args, editable=True, **kwargs):
        super().__init__(*args, **kwargs)

        self.editable = editable

        self.layout = QtWidgets.QGridLayout(self)

        title = self._title()
        if title:
            self.title = BoldQLabel(self)
            self.title.setText(translate(self.__class__.__name__, title))
            self.layout.addWidget(self.title, 0, 0, 1, 2)
        else:
            self.title = None

        self.fields = []
        self.data = None

    def _title(self):
        return None

    def _interpreted_data(self, data):
        """
        Returns a list of fields where each field is a 3-element tuple.
        Set the third element to True for input fields with only two
        elements.
        """
        return [field if len(field) == 3 else (field[0], field[1], self.editable) for field in data]

    def _no_editability_data(self, data):
        """
        Returns a list of fields with the editable property removed.
        """
        return [field if len(field) == 2 else (field[0], field[1]) for field in data]

    def setData(self, data):
        """
        Sets or updates the widget with the provided data.

        data should be a list of tuples. The first element of tuple
        will be used as the field name and the second as the field
        value. If the tuple has a third element that's False, the
        field will be read-only. Otherwise, it'll be editable.
        """
        if not data:
            return

        self.data = data

        # Creating the widgets
        for (i, (field_name, field_value, field_editable)) in enumerate(self._interpreted_data(data)):
            label = QtWidgets.QLabel(self)
            label.setText(translate(self.__class__.__name__, field_name))

            if isinstance(field_value, bool):
                edit_widget = QtWidgets.QCheckBox(self)
                edit_widget.setChecked(field_value)

                def state_changed_closure(field_name, edit_widget):
                    return lambda state: self._updateData(field_name, bool(state))
                edit_widget.stateChanged.connect(state_changed_closure(field_name, edit_widget))
            elif isinstance(field_value, str):
                edit_widget = QtWidgets.QLineEdit(self)
                edit_widget.setReadOnly(not field_editable)
                edit_widget.setText(field_value)

                def state_changed_closure(field_name, edit_widget):
                    return lambda: self._updateData(field_name, edit_widget.text())
                edit_widget.editingFinished.connect(state_changed_closure(field_name, edit_widget))
            else:
                raise(ValueError("Only string and boolean data supported. %s provided for field '%s'." % (type(field_value).__name__, field_name)))

            if len(self.fields) == i:
                self.layout.addWidget(label, i+1, 0, 1, 1)
                self.layout.addWidget(edit_widget, i+1, 1, 1, 1)
                self.fields.append([label, edit_widget])
            else:
                self.layout.replaceWidget(self.fields[i][0], label)
                self.layout.replaceWidget(self.fields[i][1], edit_widget)
                self.fields[i][0].deleteLater()
                self.fields[i][0] = label
                self.fields[i][1].deleteLater()
                self.fields[i][1] = edit_widget

        # Hiding any old widgets that haven't been set this time:
        while i + 1 < len(self.fields):
            i += 1
            self.fields[i][0].hide()
            self.fields[i][1].hide()

    def _updateData(self, field_name, field_value):
        """
        Updates the feature with changes made by the user.
        """
        for (i, (existing_field_name, existing_field_value, field_editable)) in enumerate(self._interpreted_data(self.data)):
            if existing_field_name == field_name:
                self.data[i] = (field_name, field_value)
                break

        # For updating the feature itself, strip out the editability attribute
        self.dataEdited.emit(self._no_editability_data(self.data))

    def getData(self):
        return self.data

class NonEditableBaseListForm(EditableBaseListForm):
    def __init__(self, *args, **kwargs):
        kwargs["editable"] = False
        super().__init__(*args, **kwargs)
