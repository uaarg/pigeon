from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from ..commonwidgets import EditableBaseListForm

from features import Feature


class FeatureDetailArea(EditableBaseListForm):
    featureChanged = QtCore.pyqtSignal(Feature)
    def __init__(self):
        super().__init__()
        self.feature = None
        self.dataEdited.connect(lambda data: self._editFeatureData(data))

    def _title(self):
        return "Feature Detail:"

    def _editFeatureData(self, data):
        """
        Updates the attributes of the feature object being edited,
        using the data provided from the EditableBaseListForm.
        """
        for field_name, field_value in self.feature.data.items():
            for data_name, data_value in data:
                if field_name == data_name:
                    self.feature.data[field_name] = data_value
                    break

        self.featureChanged.emit(self.feature)

    def showFeature(self, feature):
        self.feature = feature

        # Convert dictionary to list of tuples for the EditableBaseListForm
        data = [(key, value) for key, value in feature.data.items()]
        display_data = data.copy()
        display_data.append(("Position", feature.dispLatLon(), False))
        display_data.append(("Image Name", str(feature.image.name), False))
        self.setData(display_data)

    def updateFeature(self, feature):
        if feature == self.feature:
            self.showFeature(feature)