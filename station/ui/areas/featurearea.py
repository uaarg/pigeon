from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from station.ui.commonwidgets import EditableBaseListForm, BoldQLabel
from station.ui.areas import FeatureDetailArea

from station.features import BaseFeature, Feature

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

    def _getFeatureIcon(self, feature):
        if feature.picture_crop:
            cropping_rect = QtCore.QRect(QtCore.QPoint(*feature.picture_crop.top_left), QtCore.QPoint(*feature.picture_crop.bottom_right))
            try:
                original_picture = feature.picture_crop.image.pixmap_loader.getPixmapForSize(None)
            except ValueError:
                return None # Don't have the image yet: can't make a picture from the crop.
            else:
                picture = original_picture.copy(cropping_rect)
                feature.thumbnail = picture
                icon = QtGui.QIcon(picture)
                return icon
        else:
            return None

    def _updateItem(self, item, feature):
        item.feature = feature
        icon = self._getFeatureIcon(feature)
        if icon:
            item.setIcon(0, icon)
            item.setSizeHint(0, self.icon_size)
        item.setText(0, str(feature))

    def addFeature(self, feature, parent=None):
        item = QtWidgets.QTreeWidgetItem(parent or self.feature_tree)
        self._updateItem(item, feature)
        self.features[feature.id] = item

        for subfeature in feature.subfeatures():
            self.addFeature(subfeature, item)

    # def removeFeature(self, id):
    #     self.feature.pop()


    def showFeature(self, feature):
        self.feature_detail_area.showFeature(feature)
        self.feature_tree.setCurrentItem(self.features[feature.id])


    def updateFeature(self, feature, parent=None):
        item = self.features.get(feature.id)
        if item:
            self._updateItem(item, feature)
            for subfeature in feature.subfeatures():
                self.updateFeature(subfeature, item)
        else:
            self.addFeature(feature, parent)
