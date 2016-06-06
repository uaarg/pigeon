from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from ..commonwidgets import EditableBaseListForm

from features import BaseFeature, Feature

class FeatureDetailArea(EditableBaseListForm):
    featureChanged = QtCore.pyqtSignal(BaseFeature)
    clicktypeChanged = QtCore.pyqtSignal(int)

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
        for i, (field_name, field_value) in enumerate(self.feature.data):
            for data_name, data_value in data:
                if field_name == data_name:
                    self.feature.data[i] = (field_name, data_value)
                    break
        self.featureChanged.emit(self.feature)

    def showFeature(self, feature):
        self.feature = feature
        self.clicktypeChanged.emit(1)
        display_data = feature.data.copy()
        if hasattr(feature, "dispLatLon"):
            display_data.append(("Position", feature.dispLatLon(), False))
        if hasattr(feature, "dispMaxPositionDistance"):
            display_data.append(("Error", feature.dispMaxPositionDistance(), False))
        if hasattr(feature, "image") and feature.image:
            display_data.append(("Image Name", str(feature.image.name), False))
        self.setData(display_data)

    def updateFeature(self, feature):
        if feature == self.feature:
            self.showFeature(feature)
