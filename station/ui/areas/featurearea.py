from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from ..commonwidgets import EditableBaseListForm, BoldQLabel
from . import FeatureDetailArea

from features import Feature

class FeatureTree(QtWidgets.QTreeWidget):

    def __init__(self):
        super().__init__()
        #print(dir(self))
        self.feature = None
        #self.setColumnCount(1)
        #self.setHeaderLabels(['Name'])
        #parent = QtWidgets.QTreeWidgetItem(self)
        #parent.setText(0,"name of feature")
        #child2 = QtWidgets.QTreeWidgetItem(parent1)
        #child2.setText(0,'child2')
        self.expandAll()
        self.header().close()
        self.font=QtGui.QFont()
        self.font.setPointSize(14)
        self.expandAll()
        #print(dir(self))


    def iterFeatures(self):
        items = []
        root = self.invisibleRootItem()
        for index in range(root.childCount()):
            items.append(root.child(index))
        return items

    def iterSubFeatures(self, feature):
        items = []
        for index in range(feature.childCount()):
            items.append(root.child(index))
        return items

    def findFeature(self, feature):
        for item in self.iterFeatures():
            if item.feature == feature:
                return  item

    def currentlyselected(self):
        for item in self.selectedItems():
            return item

    #def addSubFeature(self, parentfeature, feature):
        #findFeature(parentfeature)

class FeatureArea(QtWidgets.QFrame):

    def __init__(self, *args, settings_data={}, features=[], minimum_width=250,**kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = settings_data

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

        self.feature_tree = FeatureTree()
        self.feature_tree.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.layout.addWidget(self.feature_tree, 1, 0, 1, 1)

        self.feature_detail_area = FeatureDetailArea()
        self.layout.addWidget(self.feature_detail_area, 2, 0, 1, 1)

    def getFeatureList(self):
        return [feature for feature in self.feature_tree.iterFeatures()]

    def addFeature(self, feature):
        if feature.isSubFeature == True:
            self.addSubFeature(feature)
        else:
            item = QtWidgets.QTreeWidgetItem(self.feature_tree)
            #item.setSizeHint(0,QtCore.QSize(75, 75)) //to cahnge size of collumn 0
            item.setText(0,str(feature))
            item.feature = feature
            item.setFont(0,self.feature_tree.font)
            feature.feature_area_item = item
            if feature.picture:
                icon = QtGui.QIcon(feature.picture)
                item.setIcon(0,icon)
            self.showFeature(feature)

    def showFeature(self, feature):
        self.feature_detail_area.showFeature(feature)
        if feature.isSubFeature == False:
            self.feature_tree.setCurrentItem(feature.feature_area_item)

    def showSubFeature(self, feature):
        self.feature_detail_area.showSubFeature(feature)
        #self.feature_tree.setCurrentItem(feature.feature_area_item)

    def updateFeature(self, feature):
        item = self.feature_tree.findFeature(feature)
        item.setText(0,str(feature))

    def addSubFeature(self, feature):
        parentfeature = self.feature_tree.currentlyselected()
        subitem = QtWidgets.QTreeWidgetItem(parentfeature)
        subitem.setText(0,feature.image.name)
        if feature.picture:
            icon = QtGui.QIcon(feature.picture)
            subitem.setIcon(0,icon)
        self.showFeature(feature)
