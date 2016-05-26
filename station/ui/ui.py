import sys
import logging
import datetime
import types
import signal # For exiting pigeon from terminal

from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from image import Image
from features import Marker, Feature
from geo import Position

from .common import PixmapLabel, WidthForHeightPixmapLabel, PixmapLabelMarker, BoldQLabel, BaseQListWidget, ListImageItem, ScaledListWidget, QueueMixin, format_duration_for_display
from .commonwidgets import EditableBaseListForm, NonEditableBaseListForm
from .pixmaploader import PixmapLoader
from .style import stylesheet
from ui import icons

THUMBNAIL_AREA_START_HEIGHT = 100
THUMBNAIL_AREA_MIN_HEIGHT = 60
INFO_AREA_MIN_WIDTH = 250
FEATURE_AREA_MIN_WIDTH = 250

class UI(QtCore.QObject, QueueMixin):
    """
    Class for the rest of the application to interface with the UI.

    This implementation of the class uses PyQt5 to provide the UI but
    theoretically, other frameworks could be used without the rest of
    the application caring, as long as this class's API is
    implemented. Or, more likely: a mock UI instance could be used in
    unit testing for easy testing of the rest of the application.
    """
    settings_changed = QtCore.pyqtSignal()

    def ExitFcn (self, signum, fram):
        # Exiting Program from the Terminal
        self.app.exit()

    def __init__(self, save_settings, load_settings, exporter, image_queue, uav, ground_control_points=[]):
        super().__init__()
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.settings_data = load_settings()
        self.features = ground_control_points # For all features, not just GCP's
        self.uav = uav

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyleSheet(stylesheet)
        self.main_window = MainWindow(self.settings_data, self.features, self.app.exit)

        self.main_window.info_area.settings_area.settings_load_requested.connect(lambda: self.main_window.info_area.settings_area.setSettings(load_settings()))
        self.main_window.info_area.settings_area.settings_load_requested.connect(self.settings_changed.emit)
        self.main_window.info_area.settings_area.settings_save_requested.connect(save_settings)
        self.main_window.info_area.settings_area.settings_save_requested.connect(self.settings_changed.emit)

        self.main_window.feature_export_requested.connect(exporter)

        self.uav.addCommandAckedCb(self.main_window.info_area.controls_area.receive_command_ack.emit)
        self.main_window.info_area.controls_area.send_command.connect(self.uav.sendCommand)

        self.uav.addUAVConnectedChangedCb(self.main_window.info_area.controls_area.uav_connection_changed.emit)
        self.uav.addUAVStatusCb(self.main_window.info_area.controls_area.receive_status_message.emit)

        self.connectQueue(image_queue, self.addImage)
        signal.signal(signal.SIGINT,self.ExitFcn)

        def print_image_clicked(image, point):
            string = "Point right clicked in image %s: %s" % (image.name, image.geoReferencePoint(point.x(), point.y()))
            print(string)
            self.logger.info(string)

        def create_new_marker(image, point):
            position = image.geoReferencePoint(point.x(), point.y())
            marker = Marker(position)

            cropping_rect = QtCore.QRect(point.x() - 40, point.x() + 40, point.y() - 40, point.y() + 40)
            marker.picture = image.pixmap_loader.getPixmapForSize(None).copy(cropping_rect)
            self.addFeature(image, marker)

        # Hooking up some inter-component behaviour
        self.main_window.main_image_area.image_clicked.connect(create_new_marker)
        self.main_window.main_image_area.image_right_clicked.connect(self.main_window.main_image_area.updateRuler)
        self.settings_changed.connect(lambda: self.main_window.main_image_area._drawPlanePlumb())

    def run(self):
        self.main_window.info_area.settings_area.settings_load_requested.emit()
        self.main_window.show()
        self.startQueueMonitoring()
        return self.app.exec_()

    def addImage(self, image):
        self.main_window.addImage(image)

    def addFeature(self, image, feature):
        feature.image = image
        self.features.append(feature)
        self.main_window.addFeature(feature)

class MainWindow(QtWidgets.QMainWindow):
    featureChanged = QtCore.pyqtSignal(Feature)
    feature_export_requested = QtCore.pyqtSignal(list,str)

    def __init__(self, settings_data={}, features=[], exitfcnCB= None):
        super().__init__()
        self.settings_data = settings_data
        self.ExitingCB = exitfcnCB
        # State
        self.current_image = None

        # Defining window properties
        self.setObjectName("main_window")
        self.showMaximized()
        self.setMinimumSize(QtCore.QSize(500, 500))
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(1)
        self.setSizePolicy(size_policy)
        self.setWindowTitle(translate("MainWindow", "Ground Imaging Station"))

        # Defining the page layout
        self.central_widget = QtWidgets.QWidget(self)
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        self.grid_layout = QtWidgets.QGridLayout(self.central_widget)
        self.grid_layout.setObjectName("grid_layout")

        self.main_vertical_split = QtWidgets.QSplitter()
        self.main_vertical_split.setOrientation(QtCore.Qt.Vertical)
        self.main_vertical_split.setObjectName("main_vertical_split")
        self.grid_layout.addWidget(self.main_vertical_split, 0, 0, 1, 1)

        self.main_horizontal_split = QtWidgets.QSplitter(self.main_vertical_split)
        self.main_horizontal_split.setOrientation(QtCore.Qt.Horizontal)
        self.main_horizontal_split.setObjectName("main_horizontal_split")
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(100)
        self.main_horizontal_split.setSizePolicy(size_policy)
        self.main_horizontal_split.setMinimumSize(QtCore.QSize(200, THUMBNAIL_AREA_START_HEIGHT))

        # Populating the page layout with the major components.
        self.info_area = InfoArea(self.main_horizontal_split, settings_data=settings_data)
        self.main_image_area = MainImageArea(self.main_horizontal_split, settings_data=settings_data, features=features)
        self.feature_area = FeatureArea(self.main_horizontal_split, settings_data=settings_data, features=features)
        self.thumbnail_area = ThumbnailArea(self.main_vertical_split, settings_data=settings_data)

        # Hooking up some inter-component benhaviour
        self.thumbnail_area.contents.currentItemChanged.connect(lambda new_item, old_item: self.showImage(new_item.image)) # Show the image that's selected
        self.feature_area.feature_list.currentItemChanged.connect(lambda new_item, old_item: self.feature_area.showFeature(new_item.feature)) # Show feature details for the selected feature

        self.feature_area.feature_detail_area.featureChanged.connect(self.featureChanged.emit) # Feature's details can be changed
        self.main_image_area.featureChanged.connect(self.featureChanged.emit)  # Feature's position can be changed when it's dragged

        self.featureChanged.connect(self.feature_area.updateFeature) # Update the feature in the list
        self.featureChanged.connect(self.main_image_area.updateFeature) # Update the feature in the main image window
        self.featureChanged.connect(self.feature_area.feature_detail_area.updateFeature) # Update the feature details

        self.initMenuBar()
        QtCore.QMetaObject.connectSlotsByName(self)

    def initMenuBar(self):
        self.menubar = self.menuBar()

        ExitAction = QtWidgets.QAction("Exit Pigeon :(", self)
        ExitAction.setShortcut('Ctrl+Q')
        ExitAction.triggered.connect(self.ExitFcn)

        AboutAction = QtWidgets.QAction("About Pigeon", self)
        AboutAction.setShortcut('Ctrl+A')
        AboutAction.triggered.connect(self.AboutPopup)

        fileMenu = self.menubar.addMenu('&File')
        fileMenu.addAction(AboutAction)
        fileMenu.addAction(ExitAction)

        KMLexport = QtWidgets.QAction("KML Export", self)
        KMLexport.triggered.connect(lambda: self.doExporting("KML"))

        CSVexport = QtWidgets.QAction("CSV Normal", self)
        CSVexport.triggered.connect(lambda: self.doExporting("CSV Normal"))

        CSVexportUSC = QtWidgets.QAction("CSV: USC", self)
        CSVexportUSC.triggered.connect(lambda: self.doExporting("CSV: USC"))

        CSVexportAUVSI = QtWidgets.QAction("CSV: AUVSI", self)
        CSVexportAUVSI.triggered.connect(lambda: self.doExporting("CSV: AUVSI"))

        fileMenu = self.menubar.addMenu('&Export')
        fileMenu.addAction(KMLexport)
        fileMenu.addAction(CSVexport)
        fileMenu.addAction(CSVexportUSC)
        fileMenu.addAction(CSVexportAUVSI)

    def ExitFcn(self):
        print("You pressed Ctrl+Q, now exiting")
        self.ExitingCB()

    def AboutPopup(self):
        print("You pressed Ctrl+S, popup is not working yet")

    def doExporting(self, text):
        try:
            self.feature_export_requested.emit(self.feature_area.getFeatureList(),text)
        except:
            print("Exporting type " + text + " is not supported!!!!!")

    def addImage(self, image):
        image.pixmap_loader = PixmapLoader(image.path)

        # Recording the width and height of the image for other code to use:
        image.width = image.pixmap_loader.width()
        image.height = image.pixmap_loader.height()

        if self.settings_data.get("Follow Images", False) or not self.current_image:
            self.showImage(image)
        self.thumbnail_area.addImage(image)
        self.info_area.addImage(image)
        image.pixmap_loader.optimizeMemory()

    def setSettings(self, settings_data):
        return self.info_area.setSettings(settings_data)

    def showImage(self, image):
        if self.current_image:
            self.current_image.pixmap_loader.freeOriginal()
            self.current_image.pixmap_loader.optimizeMemory()
        self.current_image = image
        self.current_image.pixmap_loader.holdOriginal()
        self.main_image_area.showImage(image)
        self.info_area.showImage(image)

    def addFeature(self, feature):
        self.feature_area.addFeature(feature)
        self.main_image_area.addFeature(feature)


class InfoArea(QtWidgets.QFrame):
    def __init__(self, *args, settings_data={}, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(INFO_AREA_MIN_WIDTH, 200))

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("info_area")

        self.layout = QtWidgets.QVBoxLayout(self)

        self.controls_area = ControlsArea(self)
        self.state_area = StateArea(self, editable=False)
        self.image_info_area = ImageInfoArea(self, editable=False)
        self.settings_area = SettingsArea(self)

        self.layout.addWidget(self.controls_area)
        self.layout.addWidget(self.state_area)
        self.layout.addWidget(self.image_info_area)
        self.layout.addWidget(self.settings_area)

        self.last_image_time = None
        self.image_count = 0

        # Starting a timer to update data every second
        self._updateInfo()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._updateInfo)
        self.timer.start(1000)

    def setSettings(self, settings_data):
        return self.settings_area.setData(settings_data)

    def showImage(self, image):
        """
        Updates the info area with data about the image being shown.
        """
        data = [("Image Name", image.name),
                ("Height", image.plane_position.dispHeight()),
                ("Pitch", image.plane_orientation.dispPitch()),
                ("Roll", image.plane_orientation.dispRoll()),
                ("Yaw", image.plane_orientation.dispYaw()),
                ("Plane Position", image.plane_position.dispLatLon()),]
        self.image_info_area.setData(data)

    def addImage(self, image):
        """
        Keeping track of when the last image was added and updating
        info as needed.
        """
        self.last_image_time = datetime.datetime.now()
        self.image_count += 1
        self._updateInfo()

    def _updateInfo(self):
        """
        Update the state information.
        """
        if self.last_image_time:
            timedelta = datetime.datetime.now() - self.last_image_time
            last_image_time_ago = format_duration_for_display(timedelta)
        else:
            last_image_time_ago = "(none received)"

        data = [("Image Count", str(self.image_count)),
                ("Time since last image", last_image_time_ago),]
        self.state_area.setData(data)


class MainImageArea(QtWidgets.QWidget):
    image_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    image_right_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    featureChanged = QtCore.pyqtSignal(Feature)
    rightmousepresspoint = 0

    def __init__(self, *args, settings_data={}, features=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = settings_data
        self.features = features

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalStretch(100)
        size_policy.setVerticalStretch(100)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(100, 100))

        self.setObjectName("main_image_widget")

        self.layout = QtWidgets.QVBoxLayout(self)

        # self.title = QtWidgets.QLabel()
        # self.title.setText(translate("MainImageArea", "Main Image"))
        # self.title.setAlignment(QtCore.Qt.AlignHCenter)
        # self.layout.addWidget(self.title)

        self.image_area = PixmapLabel(interactive=True)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalStretch(100)
        size_policy.setVerticalStretch(100)
        self.image_area.setSizePolicy(size_policy)
        self.image_area.setMinimumSize(QtCore.QSize(50, 50))
        self.image_area.setAlignment(QtCore.Qt.AlignHCenter)
        self.layout.addWidget(self.image_area)

        self.image = None

        # Plumbline marker (showing where directly below the plane is):
        self.plumbline = None

        # Features as drawn:
        self.feature_pixmap_label_markers = {}
        self.image_area.pixmap_label_marker_dropped.connect(self._moveFeatureById)

        self.ruler = QtCore.QLine()

    def updateRuler(self, image, point):
        if (self.ruler.dx() ==0 ) and (self.ruler.dy() == 0): # on first click
            print("Got to first click")
            self.ruler.setP1(point)  # Set new point
            print('Point 1 x = ' + str(point.x()) +'\n y = '+ str(point.y()))
            point.setX(point.x()+1) # Set changes to prep for second click
            point.setY(point.y()+1)
            print('Point 1 (+1,+1) x = ' + str(point.x()) +'\n y = '+ str(point.y()))
            self.ruler.setP2(point)
            print('dx = ' + str(self.ruler.dx()) +'\n dy = '+ str(self.ruler.dy()))
        elif (self.ruler.dx() == 1) and (self.ruler.dy() == 1): # on second click
            print('Got to second click')
            self.ruler.setP2(point) # set second point
            distance = image.distance([self.ruler.x1(), self.ruler.y1()],
                                      [self.ruler.x2(), self.ruler.y2()])
            #datPainter = QtGui.QPainter() # Probably need to add pixmap to this event, RJA, E.I.T.
            #datPainter.begin(self)
            #self._drawLine(datPainter, self.ruler, 'Ruler')
            #datPainter.end()
            print("Ruler is "+ str(distance)+ "m long.") # Add angle???
        self.showRuler(point)

    def showImage(self, image):
        self._clearFeatures()
        # clear past Ruler?
        self.image = image
        self.image_area.setPixmap(image.pixmap_loader)

        self._drawPlanePlumb()
        self._drawFeatures()

    def _drawPlanePlumb(self):
        """
        Draw a little plane icon on the image at the point directly
        below the plane. But only if this behaviour is enabled in the
        settings.
        """
        if not self.image:
            return

        if self.settings_data.get("Plane Plumbline", True):
            if not self.plumbline:
                self.plumbline = PixmapLabelMarker(self.image_area, icons.airplane)
                self.image_area.addPixmapLabelFeature(self.plumbline)

            pixel_x, pixel_y = self.image.getPlanePlumbPixel()
            if pixel_x and pixel_y:
                point = QtCore.QPoint(pixel_x, pixel_y)
                self.plumbline.moveTo(point)
                self.plumbline.show()
            else:
                self.plumbline.hide()

        elif self.plumbline:
            self.plumbline.hide()

    def _drawLine(self, datPainter, line, drwType ):
        '''
        This is the
        Used to draw the connecting line between any two points.
        '''

        if drwType == 'Ruler': # For the line of the ruler
            pen = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DashDotDotLine)
        elif drwType == 'Border': # For the border of a Meta-Marker between markers
            pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine)
        elif drwType == '':
            print('Type of Line is not supported!!')

        datPainter.setPen(pen)
        datPainter.drawLine(line.x1(), line.x2(), line.y1(), line.y2())

    def paintEvent(self, e):
        datPainter = QtGui.QPainter()
        datPainter.begin(self)
        self._drawLine(datPainter, self.ruler, 'Ruler')
        datPainter.end()

    def _clearFeatures(self):
        for pixmap_label_marker in self.feature_pixmap_label_markers.values():
            pixmap_label_marker.deleteLater()
        self.feature_pixmap_label_markers = {}

    def _drawFeature(self, feature):
        # Cleaning up any UI elements already drawn for this feature if they exist:
        old_pixmap_label_marker = self.feature_pixmap_label_markers.pop(feature.id(), None)
        if old_pixmap_label_marker:
            old_pixmap_label_marker.hide()

        if feature.position:
            pixel_x, pixel_y = self.image.invGeoReferencePoint(feature.position)
            if pixel_x and pixel_y:
                point = QtCore.QPoint(pixel_x, pixel_y)
                pixmap_label_marker = PixmapLabelMarker(self, icons.name_map[feature.icon_name], feature.icon_size, moveable=True, feature_id=feature.id())
                self.image_area.addPixmapLabelFeature(pixmap_label_marker)
                pixmap_label_marker.moveTo(point)
                pixmap_label_marker.setToolTip(str(feature))
                pixmap_label_marker.show()

                self.feature_pixmap_label_markers[feature.id()] = pixmap_label_marker


    def _drawFeatures(self):
        for feature in self.features:
            self._drawFeature(feature)

    def _moveFeatureById(self, feature_id, point):
        try:
            feature = [feature for feature in self.features if id(feature) == int(feature_id)][0]
        except IndexError:
            raise(Exception("Provided feature id of '%s' doesn't match any known features." % (feature_id,)))
        self._moveFeature(feature, point)

    def _moveFeature(self, feature, point):
        feature.updatePosition(self.image.geoReferencePoint(point.x(), point.y()))
        self._drawFeature(feature)
        self.featureChanged.emit(feature)

    def addFeature(self, feature):
        self._drawFeature(feature)

    def updateFeature(self, feature):
        self._drawFeature(feature)

    def showRuler(self, point):
        '''
        Used to draw the end icon of the Ruler
        '''
        pixmap_label_marker = PixmapLabelMarker(self.image_area, icons.end_point, offset=QtCore.QPoint(-9, -19))
        self.image_area.addPixmapLabelFeature(pixmap_label_marker)
        pixmap_label_marker.moveTo(point)
        #pixmap_label_marker.setToolTip(str(feature))
        pixmap_label_marker.show()

    def mouseReleaseEvent(self, event):
        """
        Called by Qt when the user clicks on the image.

        Emitting an image_right_clicked event with the point if it was a
        right click.
        """
        point = QtCore.QPoint(event.x(), event.y())
        point = self.image_area.pointOnOriginal(point)
        if event.button() == QtCore.Qt.LeftButton and point:
            self.image_clicked.emit(self.image, point)
        if event.button() == QtCore.Qt.RightButton and point:
            self.image_right_clicked.emit(self.image, point)


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

class FeatureArea(QtWidgets.QFrame):

    def __init__(self, *args, settings_data={}, features=[],**kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = settings_data

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(FEATURE_AREA_MIN_WIDTH, 200))

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("feature_area")

        self.title = BoldQLabel(self)
        self.title.setText(translate("FeatureArea", "Marker List:"))

        self.layout = QtWidgets.QGridLayout(self)

        self.layout.addWidget(self.title, 0, 0, 1, 1)

        self.feature_list = BaseQListWidget(self)
        self.feature_list.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.feature_list.setFlow(QtWidgets.QListWidget.TopToBottom)
        self.layout.addWidget(self.feature_list, 1, 0, 1, 1)

        self.feature_detail_area = FeatureDetailArea()
        self.layout.addWidget(self.feature_detail_area, 2, 0, 1, 1)

        '''
        # Compairing Choice shows all GCP's
        self.CompairingChoice = QtWidgets.QComboBox(self)
        self.CompairingChoice.resize(self.CompairingChoice.minimumSizeHint())

        for confirmedPoint in features:
            self.CompairingChoice.addItem(confirmedPoint.data[0][1])
        self.CompairingChoice.activated[str].connect(self.doErrorCheck)

        print("We have "+str(self.CompairingChoice.count())+" GCP's")
        self.layout.addWidget(self.CompairingChoice)
        '''


        '''
        self.ExportingChoice = QtWidgets.QComboBox(self) #Drop down menu
        self.ExportingChoice.resize(self.ExportingChoice.minimumSizeHint())
        self.ExportingChoice.addItem("KML") # Normal KML exporting
        self.ExportingChoice.addItem("CSV Normal") # CSV export with the existing marker features
        self.ExportingChoice.addItem("CSV: USC") # Exporting for USC 2016 results
        self.ExportingChoice.addItem("CSV: AUVSI") # Exporting for AUVSI 2016 results
        self.layout.addWidget(self.ExportingChoice)
        self.ExportingChoice.setCurrentIndex(1) # Default Export is CSV

        self.export_button = QtWidgets.QPushButton("Execute Export", self)
        self.export_button.resize(self.export_button.minimumSizeHint())
        self.layout.addWidget(self.export_button)

        self.export_button.clicked.connect(self.doExporting)

    def doExporting(self):
        text= self.ExportingChoice.currentText()
        print((self.getFeatureList()))
        print(text)
        try:
            self.feature_export_requested.emit(self.getFeatureList(),text)
        except:
            print("Exporting type " + text + " is not supported!!!!!")

        
    def doErrorCheck(self):
        text= self.CompairingChoice.currentText()

        self.error_check_requested.emit(feature,text)
        for confirmedPoint in features:
            if(confirmedPoint.data[0][1]== self.CompairingChoice.currentText()):
                print(dir(confirmedPoint.data))
        #populate marker thing as GCP's Position
    '''
    def getFeatureList(self):
        return [feature for feature in self.feature_list.iterItems()]

    def addFeature(self, feature):
        item = QtWidgets.QListWidgetItem("", self.feature_list)
        item.setText(str(feature))
        item.feature = feature
        feature.feature_area_item = item
        if feature.picture:
            icon = QtGui.QIcon(feature.picture)
            item.setIcon(icon)
        self.showFeature(feature)

    def showFeature(self, feature):
        self.feature_detail_area.showFeature(feature)
        self.feature_list.setCurrentItem(feature.feature_area_item)

    def updateFeature(self, feature):
        for item in self.feature_list.iterItems():
            if item.feature == feature:
                item.setText(str(feature))
                break



class ThumbnailArea(QtWidgets.QWidget):
    def __init__(self, *args, settings_data={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.settings_data = settings_data

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(10)
        size_policy.setVerticalStretch(10)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(200, THUMBNAIL_AREA_MIN_HEIGHT))

        self.setObjectName("thumbnail_area")
        self.layout = QtWidgets.QHBoxLayout(self)

        self.contents = ScaledListWidget()
        self.contents.setFlow(QtWidgets.QListWidget.LeftToRight)
        self.layout.addWidget(self.contents)

        self.recent_image = WidthForHeightPixmapLabel()
        self.layout.addWidget(self.recent_image)

        # self.setFrameShape(QtWidgets.QFrame.NoFrame)

        # self.title = QtWidgets.QLabel(self)
        # self.title.setText(translate("ThumbnailArea", "Thumbnail List"))

        self.images = []


    def addImage(self, image, index=None):
        if index:
            raise(NotImplementedError())

        item = ListImageItem(image.pixmap_loader, self.contents)
        item.image = image

        if self.settings_data.get("Follow Images", False):
            item.setSelected(True)
            self.contents.scrollToItem(item)

        self.logger.debug("Setting recent image pixmap")
        self.recent_image.setPixmap(image.pixmap_loader)
        self.recent_image.image = image

class ImageInfoArea(NonEditableBaseListForm):
    def _title(self):
        return "Image:"

class StateArea(NonEditableBaseListForm):
    def _title(self):
        return "State:"


def markMessageReceived(func=None):
    """
    Marks that a message has been received from the UAV. Function
    decorator for methods who's class has a last_message_received_time
    attribute.
    """
    def new_func(*args, **kwargs):
        args[0].last_message_received_time = datetime.datetime.now()
        func(*args, **kwargs)
    return new_func

class ControlsArea(QtWidgets.QWidget):
    send_command = QtCore.pyqtSignal(str, str)
    receive_command_ack = QtCore.pyqtSignal(str, str)
    receive_status_message = QtCore.pyqtSignal(dict)

    uav_connection_changed = QtCore.pyqtSignal(bool)

    RUN_STOP = "0"
    RUN_PAUSE = "1"
    RUN_PLAY = "2"

    RUN_CHOICES = ((RUN_STOP, "Stopped"),
                   (RUN_PAUSE, "Paused"),
                   (RUN_PLAY, "Running"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.title = BoldQLabel(self)
        self.title.setText(translate("ControlsArea", "UAV:"))
        self.layout.addWidget(self.title)

        self.uav_status_form = NonEditableBaseListForm()
        self.layout.addWidget(self.uav_status_form)

        self.uav_connected = "No"
        self.last_message_received_time = None
        self.uav_pictures_taken = ""
        self.uav_pictures_transmitted = ""

        run_buttons_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(run_buttons_layout)

        self.run_value = self.RUN_STOP
        self.play_icon = QtGui.QIcon(icons.play)
        self.pause_icon = QtGui.QIcon(icons.pause)

        self.stop_button = QtWidgets.QPushButton(QtGui.QIcon(icons.stop), "", self)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        run_buttons_layout.addWidget(self.stop_button)

        self.play_pause_button = QtWidgets.QPushButton(self.play_icon, "", self)
        self.play_pause_button.clicked.connect(self.play_pause_button_clicked)
        run_buttons_layout.addWidget(self.play_pause_button)

        self.run_value_label = QtWidgets.QLabel()
        run_buttons_layout.addWidget(self.run_value_label)

        self.receive_command_ack.connect(self.receiveCommandAck)
        self.uav_connection_changed.connect(self.updateUAVConnection)
        self.receive_status_message.connect(self.receiveStatusMessage)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._updateDisplayedInfo)
        self.timer.start(1000)

    def stop_button_clicked(self):
        self.send_command.emit("RUN", self.RUN_STOP)

    def play_pause_button_clicked(self):
        new_value = self._getToggledRunValue()
        self.send_command.emit("RUN", new_value)

    def _updateRunValue(self, value):
        if value != self.RUN_PLAY:
            self.play_pause_button.setIcon(self.play_icon)
        else:
            self.play_pause_button.setIcon(self.pause_icon)

        if value == self.RUN_STOP:
            self.stop_button.setEnabled(False)
        else:
            self.stop_button.setEnabled(True)

        self.run_value = value

        self.run_value_label.setText(self.get_RUN_display())

    def _getToggledRunValue(self):
        if self.run_value == self.RUN_PLAY:
            return self.RUN_PAUSE
        else:
            return self.RUN_PLAY

    def get_RUN_display(self):
        return dict(self.RUN_CHOICES).get(self.run_value)

    @markMessageReceived
    def receiveCommandAck(self, command, value):
        if command == "RUN":
            self._updateRunValue(value)

    def _updateDisplayedInfo(self):
        if self.last_message_received_time:
            time_since_last_message = format_duration_for_display(datetime.datetime.now() - self.last_message_received_time)
        else:
            time_since_last_message = "(never)"
        data = [("UAV Connected", self.uav_connected),
                ("Time since last message", time_since_last_message),
                ("Pictures captured", self.uav_pictures_taken),
                ("Pictures transmitted", self.uav_pictures_transmitted),
               ]
        self.uav_status_form.setData(data)

    def updateUAVConnection(self, connected):
        if connected:
            self.uav_connected = "Yes"
        else:
            self.uav_connected = "No"
        self._updateDisplayedInfo()

    @markMessageReceived
    def receiveStatusMessage(self, status_dict):
        self._updateDisplayedInfo()
        self.uav_pictures_taken = status_dict.get("TAKEN", "")
        self.uav_pictures_transmitted = status_dict.get("TRANS", "")



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
