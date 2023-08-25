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
        Returns a copy of the provided list of fields except with each
        field extended to be a 4-element tuple if not already.
        If the third element (choices) doesn't exist, sets it to an empty
        list. If the fourth element (editable) doesn't exist, sets it
        according to self.editable
        """
        output = []
        for field in data:
            if len(field) == 2:
                field = (field[0], field[1], [], self.editable)
            elif len(field) == 3:
                field = (field[0], field[1], field[2], self.editable)
            output.append(field)

        return output

    def setData(self, data):
        """
        Sets or updates the widget with the provided data.

        data should be a list of tuples:
          * The first element of the tuple will be used as the field name.
          * The second element of the tuple as the field value.
          * If the tuple has a third element, it should be a list of strings
            and a selector UI element will be populated with these values.
          * If the tuple has a fourth element, it determines whether the
            field is editable or not: True means editable, False means readonly.
            If this element does not exist, the detault provided when
            instantiating this class will be used.
        """
        if not data:
            return

        self.data = data

        # Creating the widgets
        for (i, (field_name, field_value, field_choices,
                 field_editable)) in enumerate(self._interpreted_data(data)):
            label = QtWidgets.QLabel(self)
            label.setText(translate(self.__class__.__name__, field_name))

            if isinstance(field_value, bool):
                edit_widget = QtWidgets.QCheckBox(self)
                edit_widget.setChecked(field_value)
                edit_widget.setEnabled(field_editable)

                def state_changed_closure(field_name):
                    return lambda state: self._updateData(
                        field_name, bool(state))

                edit_widget.stateChanged.connect(
                    state_changed_closure(field_name))
            elif isinstance(field_value, str):
                if field_choices and field_editable:
                    edit_widget = QtWidgets.QComboBox(self)
                    edit_widget.addItems(field_choices)
                    edit_widget.setCurrentText(field_value)

                    def state_changed_closure(field_name, field_choices):
                        return lambda index: self._updateData(
                            field_name, field_choices[index])

                    edit_widget.currentIndexChanged.connect(
                        state_changed_closure(field_name, field_choices))

                else:
                    edit_widget = QtWidgets.QLineEdit(self)
                    edit_widget.setReadOnly(not field_editable)
                    edit_widget.setText(field_value)

                    def state_changed_closure(field_name, edit_widget):
                        return lambda: self._updateData(
                            field_name, edit_widget.text())

                    edit_widget.editingFinished.connect(
                        state_changed_closure(field_name, edit_widget))
            else:
                raise (ValueError(
                    "Only string and boolean data supported. %s provided for field '%s'."
                    % (type(field_value).__name__, field_name)))

            if len(self.fields) == i:
                self.layout.addWidget(label, i + 1, 0, 1, 1)
                self.layout.addWidget(edit_widget, i + 1, 1, 1, 1)
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
        for (i, (existing_field_name, existing_field_value, _,
                 _)) in enumerate(self._interpreted_data(self.data)):
            if existing_field_name == field_name:
                data = list(self.data[i])
                data[1] = field_value
                self.data[i] = tuple(data)

        self.dataEdited.emit(self.data)

    def getData(self):
        return self.data


class NonEditableBaseListForm(EditableBaseListForm):

    def __init__(self, *args, **kwargs):
        kwargs["editable"] = False
        super().__init__(*args, **kwargs)
