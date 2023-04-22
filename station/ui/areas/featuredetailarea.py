from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from ..commonwidgets import EditableBaseListForm, BoldQLabel

from features import BaseFeature, Feature

class FeatureDetailArea(QtWidgets.QWidget):
    featureChanged = QtCore.pyqtSignal(BaseFeature)
    addSubfeatureRequested = QtCore.pyqtSignal(BaseFeature)

    def __init__(self):
        super().__init__()

        self.feature = None

        self.layout = QtWidgets.QVBoxLayout()

        self.title = BoldQLabel(self)
        self.title.setText(translate("FeatureDetailArea", "Feature Detail:"))
        self.layout.addWidget(self.title)

        self.edit_form = EditableBaseListForm(self)
        self.layout.addWidget(self.edit_form)

        self.edit_form.dataEdited.connect(lambda data: self._editFeatureData(data))

        self.setLayout(self.layout)

        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        self.add_subfeature_button = QtWidgets.QPushButton(translate("FeatureDetailArea", "Add Subfeature"), self)
        self.buttons_layout.addWidget(self.add_subfeature_button)
        # Causes crash - Mackenzie
        #self.add_subfeature_button.clicked.connect(lambda: self.addSubfeatureRequested.emit(self.feature))

    def _editFeatureData(self, data):
        """
        Updates the attributes of the feature object being edited,
        using the data provided from the EditableBaseListForm.
        """
        for i, feature_field in enumerate(self.feature.data):
            for data_field in data:
                if feature_field[0] == data_field[0]:
                    new_field = list(feature_field)
                    new_field[1] = data_field[1]
                    self.feature.data[i] = tuple(new_field)
                    break
        self.featureChanged.emit(self.feature)

    def showFeature(self, feature):
        self.feature = feature
        display_data = feature.data.copy()
        if hasattr(feature, "dispLatLon"):
            display_data.append(("Position", feature.dispLatLon(), [], False))
        if hasattr(feature, "dispMaxPositionDistance"):
            display_data.append(("Error", feature.dispMaxPositionDistance(), [], False))
        if hasattr(feature, "image") and feature.image:
            display_data.append(("Image Name", str(feature.image.name), [], False))
        self.edit_form.setData(display_data)
        if self.feature.allowSubfeatures():
            self.add_subfeature_button.show()
        else:
            self.add_subfeature_button.hide()

    def updateFeature(self, feature):
        if feature.id == self.feature.id:
            self.showFeature(feature)