from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from ..commonwidgets import EditableBaseListForm

from features import Feature


class FeatureDetailArea(EditableBaseListForm):
    featureChanged = QtCore.pyqtSignal(Feature)
    clicktypeChanged = QtCore.pyqtSignal(int)
    addingsubfeature = QtCore.pyqtSignal(Feature)

    def __init__(self):
        super().__init__()
        self.feature = None
        self.dataEdited.connect(lambda data: self._editFeatureData(data))
        self.add_subfeature = QtWidgets.QPushButton("Add Subfeature", self)
        self.add_subfeature.resize(self.add_subfeature.minimumSizeHint())
        self.add_subfeature.clicked.connect(lambda: self.clicktypeChanged.emit(2))
        #print(dir(self.add_subfeature.clicked))

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
        self.clicktypeChanged.emit(1)
        # Convert dictionary to list of tuples for the EditableBaseListForm
        data = [(key, value) for key, value in feature.data.items()]
        display_data = data.copy()
        display_data.append(("Position", feature.dispLatLon(), False))
        display_data.append(("Image Name", str(feature.image.name), False))
        self.setData(display_data)
        self.layout.addWidget(self.add_subfeature)

    def updateFeature(self, feature):
        if feature == self.feature:
            self.showFeature(feature)
