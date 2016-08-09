from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from ..commonwidgets import EditableBaseListForm, BoldQLabel
from . import FeatureDetailArea

from features import BaseFeature, Feature

class FeatureArea(QtWidgets.QFrame):
    featureSelectionChanged = QtCore.pyqtSignal(BaseFeature)

    def __init__(self, *args, settings_data={}, minimum_width=250,**kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = settings_data
        self.features = {} # Mapping from feature id's to items.

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(minimum_width, 200))

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("feature_area")

        self.title = BoldQLabel(self)
        self.title.setText(translate("FeatureArea", "Marker List:"))

        self.layout = QtWidgets.QGridLayout(self)

        self.layout.addWidget(self.title, 0, 0, 1, 1)

        self.feature_tree = QtWidgets.QTreeWidget()
        self.feature_tree.header().close()

        self.feature_tree.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.icon_size = QtCore.QSize(40, 40)
        self.feature_tree.setIconSize(self.icon_size)
        self.layout.addWidget(self.feature_tree, 1, 0, 1, 1)

        self.feature_detail_area = FeatureDetailArea()
        self.layout.addWidget(self.feature_detail_area, 2, 0, 1, 1)

        self.feature_tree.currentItemChanged.connect(lambda current, previous: self.featureSelectionChanged.emit(current.feature))
        self.featureSelectionChanged.connect(self.feature_detail_area.showFeature)

    def addFeature(self, feature, parent=None):
        item = QtWidgets.QTreeWidgetItem(parent or self.feature_tree)
        item.feature = feature
        if feature.picture:
            icon = QtGui.QIcon(feature.picture)
            item.setIcon(0, icon)
            item.setSizeHint(0, self.icon_size)
        item.setText(0, str(feature))

        self.features[feature.id] = item

        for subfeature in feature.subfeatures():
            self.addFeature(subfeature, item)

    def showFeature(self, feature):
        self.feature_detail_area.showFeature(feature)
        self.feature_tree.setCurrentItem(self.features[feature.id])

    def updateFeature(self, feature, parent=None):
        item = self.features.get(feature.id)
        if item:
            item.setText(0, str(feature))
            item.feature = feature
            for subfeature in feature.subfeatures():
                self.updateFeature(subfeature, item)
        else:
            self.addFeature(feature, parent)