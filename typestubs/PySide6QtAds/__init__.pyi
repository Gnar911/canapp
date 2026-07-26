import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtWidgets
from __future__ import annotations
import collections.abc
import enum
import platform as platform
import typing
from . import PySide6QtAds
__all__: list[str] = ['AllDockAreas', 'AutoHideIcon', 'BitwiseAnd', 'BitwiseOr', 'BottomDockWidgetArea', 'CDockAreaTabBar', 'CDockAreaTitleBar', 'CDockAreaWidget', 'CDockComponentsFactory', 'CDockContainerWidget', 'CDockFocusController', 'CDockManager', 'CDockOverlay', 'CDockOverlayCross', 'CDockSplitter', 'CDockWidget', 'CDockWidgetTab', 'CDockingStateReader', 'CElidingLabel', 'CFloatingDockContainer', 'CFloatingDragPreview', 'CIconProvider', 'CSpacerWidget', 'CTitleBarButton', 'CenterDockWidgetArea', 'DockAreaCloseIcon', 'DockAreaMenuIcon', 'DockAreaMinimizeIcon', 'DockAreaUndockIcon', 'DockWidgetArea', 'DraggingFloatingWidget', 'DraggingInactive', 'DraggingMousePressed', 'DraggingTab', 'IFloatingWidget', 'IconCount', 'InvalidDockWidgetArea', 'LeftDockWidgetArea', 'NoDockWidgetArea', 'OuterDockAreas', 'PySide6QtAds', 'RightDockWidgetArea', 'SideBarBottom', 'SideBarLeft', 'SideBarNone', 'SideBarRight', 'SideBarTop', 'TabCloseIcon', 'TabDefaultInsertIndex', 'TabInvalidIndex', 'TitleBarButtonAutoHide', 'TitleBarButtonClose', 'TitleBarButtonMinimize', 'TitleBarButtonTabsMenu', 'TitleBarButtonUndock', 'TopDockWidgetArea', 'ads', 'platform']
class CDockAreaTabBar(PySide6.QtWidgets.QScrollArea):
    """
    CDockAreaTabBar(self, parent: PySide6QtAds.ads.CDockAreaWidget, /) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockAreaTabBar" inherits "QScrollArea":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def currentChanged(*args, **kwargs):
        ...
    @staticmethod
    def currentChanging(*args, **kwargs):
        ...
    @staticmethod
    def elidedChanged(*args, **kwargs):
        ...
    @staticmethod
    def removingTab(*args, **kwargs):
        ...
    @staticmethod
    def tabBarClicked(*args, **kwargs):
        ...
    @staticmethod
    def tabCloseRequested(*args, **kwargs):
        ...
    @staticmethod
    def tabClosed(*args, **kwargs):
        ...
    @staticmethod
    def tabInserted(*args, **kwargs):
        ...
    @staticmethod
    def tabMoved(*args, **kwargs):
        ...
    @staticmethod
    def tabOpened(*args, **kwargs):
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, parent: PySide6QtAds.ads.CDockAreaWidget, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def areTabsOverflowing(self) -> bool:
        ...
    def closeTab(self, Index: int) -> None:
        ...
    def count(self) -> int:
        ...
    def currentIndex(self) -> int:
        ...
    def currentTab(self) -> ads.CDockWidgetTab:
        ...
    def eventFilter(self, watched: PySide6.QtCore.QObject, event: PySide6.QtCore.QEvent) -> bool:
        ...
    def insertTab(self, Index: int, Tab: ads.CDockWidgetTab) -> None:
        ...
    def isTabOpen(self, Index: int) -> bool:
        ...
    def minimumSizeHint(self) -> PySide6.QtCore.QSize:
        ...
    def removeTab(self, Tab: ads.CDockWidgetTab) -> None:
        ...
    def setCurrentIndex(self, Index: int) -> None:
        ...
    def sizeHint(self) -> PySide6.QtCore.QSize:
        ...
    def tab(self, Index: int) -> ads.CDockWidgetTab:
        ...
    def tabAt(self, Pos: PySide6.QtCore.QPoint) -> int:
        ...
    def tabInsertIndexAt(self, Pos: PySide6.QtCore.QPoint) -> int:
        ...
    def wheelEvent(self, Event: PySide6.QtGui.QWheelEvent) -> None:
        ...
class CDockAreaTitleBar(PySide6.QtWidgets.QFrame):
    """
    CDockAreaTitleBar(self, parent: PySide6QtAds.ads.CDockAreaWidget, /) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockAreaTitleBar" inherits "QFrame":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def tabBarClicked(*args, **kwargs):
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, parent: PySide6QtAds.ads.CDockAreaWidget, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def autoHideTitleLabel(self) -> ads.CElidingLabel:
        ...
    def buildContextMenu(self, arg__1: PySide6.QtWidgets.QMenu) -> PySide6.QtWidgets.QMenu:
        ...
    def button(self, which: ads.TitleBarButton) -> ads.CTitleBarButton:
        ...
    def contextMenuEvent(self, event: PySide6.QtGui.QContextMenuEvent) -> None:
        ...
    def dockAreaWidget(self) -> ads.CDockAreaWidget:
        ...
    def indexOf(self, widget: PySide6.QtWidgets.QWidget) -> int:
        ...
    def insertWidget(self, index: int, widget: PySide6.QtWidgets.QWidget) -> None:
        ...
    def isAutoHide(self) -> bool:
        ...
    def markTabsMenuOutdated(self) -> None:
        ...
    def mouseDoubleClickEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def mouseMoveEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def mousePressEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def mouseReleaseEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
        ...
    def setAreaFloating(self) -> None:
        ...
    def setVisible(self, Visible: bool) -> None:
        ...
    def showAutoHideControls(self, Show: bool) -> None:
        ...
    def tabBar(self) -> ads.CDockAreaTabBar:
        ...
    def titleBarButtonToolTip(self, Button: ads.TitleBarButton) -> str:
        ...
    def updateDockWidgetActionsButtons(self) -> None:
        ...
class CDockAreaWidget(PySide6.QtWidgets.QFrame):
    """
    CDockAreaWidget(self, DockManager: PySide6QtAds.ads.CDockManager, parent: PySide6QtAds.ads.CDockContainerWidget, /) -> None
    """
    class eDockAreaFlag(enum.IntFlag):
        """
        An enumeration.
        """
        DefaultFlags: typing.ClassVar[ads.CDockAreaWidget.eDockAreaFlag]  # value = <eDockAreaFlag.DefaultFlags: 0>
        HideSingleWidgetTitleBar: typing.ClassVar[ads.CDockAreaWidget.eDockAreaFlag]  # value = <eDockAreaFlag.HideSingleWidgetTitleBar: 1>
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockAreaWidget" inherits "QFrame":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def currentChanged(*args, **kwargs):
        ...
    @staticmethod
    def currentChanging(*args, **kwargs):
        ...
    @staticmethod
    def tabBarClicked(*args, **kwargs):
        ...
    @staticmethod
    def viewToggled(*args, **kwargs):
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, DockManager: PySide6QtAds.ads.CDockManager, parent: PySide6QtAds.ads.CDockContainerWidget, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def addDockWidget(self, DockWidget: ads.CDockWidget) -> None:
        ...
    def allowedAreas(self) -> ads.DockWidgetArea:
        ...
    def autoHideDockContainer(self) -> ads.CAutoHideDockContainer:
        ...
    def closeArea(self) -> None:
        ...
    def closeOtherAreas(self) -> None:
        ...
    def containsCentralWidget(self) -> bool:
        ...
    def contentAreaGeometry(self) -> PySide6.QtCore.QRect:
        ...
    def currentDockWidget(self) -> ads.CDockWidget:
        ...
    def currentIndex(self) -> int:
        ...
    def dockAreaFlags(self) -> ads.CDockAreaWidget.eDockAreaFlag:
        ...
    def dockContainer(self) -> ads.CDockContainerWidget:
        ...
    def dockManager(self) -> ads.CDockManager:
        ...
    def dockWidget(self, Index: int) -> ads.CDockWidget:
        ...
    def dockWidgets(self) -> list[ads.CDockWidget]:
        ...
    def dockWidgetsCount(self) -> int:
        ...
    def features(self, /, Mode: ads.eBitwiseOperator = ...) -> ads.CDockWidget.DockWidgetFeature:
        ...
    def hideAreaWithNoVisibleContent(self) -> None:
        ...
    def index(self, DockWidget: ads.CDockWidget) -> int:
        ...
    def indexOfFirstOpenDockWidget(self) -> int:
        ...
    def insertDockWidget(self, index: int, DockWidget: ads.CDockWidget, /, Activate: bool = True) -> None:
        ...
    def internalSetCurrentDockWidget(self, DockWidget: ads.CDockWidget) -> None:
        ...
    def isAutoHide(self) -> bool:
        ...
    def isCentralWidgetArea(self) -> bool:
        ...
    def isTopLevelArea(self) -> bool:
        ...
    def markTitleBarMenuOutdated(self) -> None:
        ...
    def minimumSizeHint(self) -> PySide6.QtCore.QSize:
        ...
    def nextOpenDockWidget(self, DockWidget: ads.CDockWidget) -> ads.CDockWidget:
        ...
    def openDockWidgetsCount(self) -> int:
        ...
    def openedDockWidgets(self) -> list[ads.CDockWidget]:
        ...
    def parentSplitter(self) -> ads.CDockSplitter:
        ...
    def removeDockWidget(self, DockWidget: ads.CDockWidget) -> None:
        ...
    def saveState(self, Stream: PySide6.QtCore.QXmlStreamWriter) -> None:
        ...
    def setAllowedAreas(self, areas: ads.DockWidgetArea) -> None:
        ...
    def setAutoHide(self, Enable: bool, /, Location: ads.SideBarLocation = ..., TabIndex: int = -1) -> None:
        ...
    def setAutoHideDockContainer(self, AutoHideDockContainer: ads.CAutoHideDockContainer) -> None:
        ...
    def setCurrentDockWidget(self, DockWidget: ads.CDockWidget) -> None:
        ...
    def setCurrentIndex(self, index: int) -> None:
        ...
    def setDockAreaFlag(self, Flag: ads.CDockAreaWidget.eDockAreaFlag, On: bool) -> None:
        ...
    def setDockAreaFlags(self, Flags: ads.CDockAreaWidget.eDockAreaFlag) -> None:
        ...
    def setFloating(self) -> None:
        ...
    def setVisible(self, Visible: bool) -> None:
        ...
    def titleBar(self) -> ads.CDockAreaTitleBar:
        ...
    def titleBarButton(self, which: ads.TitleBarButton) -> PySide6.QtWidgets.QAbstractButton:
        ...
    def titleBarGeometry(self) -> PySide6.QtCore.QRect:
        ...
    def toggleAutoHide(self, /, Location: ads.SideBarLocation = ...) -> None:
        ...
    def toggleDockWidgetView(self, DockWidget: ads.CDockWidget, Open: bool) -> None:
        ...
    def toggleView(self, Open: bool) -> None:
        ...
    def updateTitleBarButtonVisibility(self, IsTopLevel: bool) -> None:
        ...
    def updateTitleBarVisibility(self) -> None:
        ...
    def updateWindowTitle(self) -> None:
        ...
class CDockComponentsFactory(Shiboken.Object):
    """
    CDockComponentsFactory(self, /) -> None
    """
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def resetDefaultFactory() -> None:
        ...
    @staticmethod
    def setFactory(Factory: ads.CDockComponentsFactory) -> None:
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def createDockAreaTabBar(self, DockArea: ads.CDockAreaWidget) -> ads.CDockAreaTabBar:
        ...
    def createDockAreaTitleBar(self, DockArea: ads.CDockAreaWidget) -> ads.CDockAreaTitleBar:
        ...
    def createDockWidgetSideTab(self, DockWidget: ads.CDockWidget) -> ads.CAutoHideTab:
        ...
    def createDockWidgetTab(self, DockWidget: ads.CDockWidget) -> ads.CDockWidgetTab:
        ...
class CDockContainerWidget(PySide6.QtWidgets.QFrame):
    """
    CDockContainerWidget(self, DockManager: PySide6QtAds.ads.CDockManager, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockContainerWidget" inherits "QFrame":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def autoHideWidgetCreated(*args, **kwargs):
        ...
    @staticmethod
    def dockAreaViewToggled(*args, **kwargs):
        ...
    @staticmethod
    def dockAreasAdded(*args, **kwargs):
        ...
    @staticmethod
    def dockAreasRemoved(*args, **kwargs):
        ...
    @staticmethod
    def floatingWidgetFromDropEvent(e: PySide6.QtGui.QDropEvent, DockManager: ads.CDockManager) -> ads.CFloatingDockContainer:
        ...
    @staticmethod
    def showDropOverlays(DockManager: ads.CDockManager, TopContainer: ads.CDockContainerWidget, GlobalPos: PySide6.QtCore.QPoint, ContentPinnable: bool) -> None:
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, DockManager: PySide6QtAds.ads.CDockManager, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def addDockArea(self, DockAreaWidget: ads.CDockAreaWidget, /, area: ads.DockWidgetArea = ...) -> None:
        ...
    def addDockWidget(self, area: ads.DockWidgetArea, Dockwidget: ads.CDockWidget, /, DockAreaWidget: PySide6QtAds.ads.CDockAreaWidget | None = None, Index: int = -1) -> ads.CDockAreaWidget:
        ...
    def autoHideSideBar(self, area: ads.SideBarLocation) -> ads.CAutoHideSideBar:
        ...
    def autoHideWidgets(self) -> list[ads.CAutoHideDockContainer]:
        ...
    def closeOtherAreas(self, KeepOpenArea: ads.CDockAreaWidget) -> None:
        ...
    def contentRect(self) -> PySide6.QtCore.QRect:
        ...
    def contentRectGlobal(self) -> PySide6.QtCore.QRect:
        ...
    def createAndSetupAutoHideContainer(self, area: ads.SideBarLocation, DockWidget: ads.CDockWidget, /, TabIndex: int = -1) -> ads.CAutoHideDockContainer:
        ...
    def createRootSplitter(self) -> None:
        ...
    def createSideTabBarWidgets(self) -> None:
        ...
    def dockArea(self, Index: int) -> ads.CDockAreaWidget:
        ...
    def dockAreaAt(self, GlobalPos: PySide6.QtCore.QPoint) -> ads.CDockAreaWidget:
        ...
    def dockAreaCount(self) -> int:
        ...
    def dockManager(self) -> ads.CDockManager:
        ...
    def dockWidgets(self) -> list[ads.CDockWidget]:
        ...
    def dragEnterEvent(self, e: PySide6.QtGui.QDragEnterEvent) -> None:
        ...
    def dragLeaveEvent(self, e: PySide6.QtGui.QDragLeaveEvent) -> None:
        ...
    def dragMoveEvent(self, e: PySide6.QtGui.QDragMoveEvent) -> None:
        ...
    def dropEvent(self, e: PySide6.QtGui.QDropEvent) -> None:
        ...
    def dropFloatingWidget(self, FloatingWidget: ads.CFloatingDockContainer, TargetPos: PySide6.QtCore.QPoint) -> None:
        ...
    def dropWidget(self, Widget: PySide6.QtWidgets.QWidget, DropArea: ads.DockWidgetArea, TargetAreaWidget: ads.CDockAreaWidget, /, TabIndex: int = -1) -> None:
        ...
    def dumpLayout(self) -> None:
        ...
    def event(self, e: PySide6.QtCore.QEvent) -> bool:
        ...
    def features(self) -> ads.CDockWidget.DockWidgetFeature:
        ...
    def floatingWidget(self) -> ads.CFloatingDockContainer:
        ...
    def handleAutoHideWidgetEvent(self, e: PySide6.QtCore.QEvent, w: PySide6.QtWidgets.QWidget) -> None:
        ...
    def hasOpenDockAreas(self) -> bool:
        ...
    def hasTopLevelDockWidget(self) -> bool:
        ...
    def isFloating(self) -> bool:
        ...
    def isInFrontOf(self, Other: ads.CDockContainerWidget) -> bool:
        ...
    def lastAddedDockAreaWidget(self, area: ads.DockWidgetArea) -> ads.CDockAreaWidget:
        ...
    def openedDockAreas(self) -> list[ads.CDockAreaWidget]:
        ...
    def openedDockWidgets(self) -> list[ads.CDockWidget]:
        ...
    def registerAutoHideWidget(self, AutoHideWidget: ads.CAutoHideDockContainer) -> None:
        ...
    def removeAutoHideWidget(self, AutoHideWidget: ads.CAutoHideDockContainer) -> None:
        ...
    def removeDockArea(self, area: ads.CDockAreaWidget) -> None:
        ...
    def removeDockWidget(self, Dockwidget: ads.CDockWidget) -> None:
        ...
    def rootSplitter(self) -> ads.CDockSplitter:
        ...
    def saveState(self, Stream: PySide6.QtCore.QXmlStreamWriter) -> None:
        ...
    def topLevelDockArea(self) -> ads.CDockAreaWidget:
        ...
    def topLevelDockWidget(self) -> ads.CDockWidget:
        ...
    def updateSplitterHandles(self, splitter: PySide6.QtWidgets.QSplitter) -> None:
        ...
    def visibleDockAreaCount(self) -> int:
        ...
    def zOrderIndex(self) -> int:
        ...
class CDockFocusController(PySide6.QtCore.QObject):
    """
    CDockFocusController(self, DockManager: PySide6QtAds.ads.CDockManager, /) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockFocusController" inherits "QObject":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, DockManager: PySide6QtAds.ads.CDockManager, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def clearDockWidgetFocus(self, dockWidget: ads.CDockWidget) -> None:
        ...
    def focusedDockArea(self) -> ads.CDockAreaWidget:
        ...
    def focusedDockWidget(self) -> ads.CDockWidget:
        ...
    def notifyFloatingWidgetDrop(self, FloatingWidget: ads.CFloatingDockContainer) -> None:
        ...
    def notifyWidgetOrAreaRelocation(self, RelocatedWidget: PySide6.QtWidgets.QWidget) -> None:
        ...
    def setDockWidgetFocused(self, focusedNow: ads.CDockWidget) -> None:
        ...
    def setDockWidgetTabFocused(self, Tab: ads.CDockWidgetTab) -> None:
        ...
    def setDockWidgetTabPressed(self, Value: bool) -> None:
        ...
class CDockManager(ads.CDockContainerWidget):
    """
    CDockManager(self, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
    """
    class ColorSchemeMode(enum.IntEnum):
        """
        An enumeration.
        """
        Dark: typing.ClassVar[ads.CDockManager.ColorSchemeMode]  # value = <ColorSchemeMode.Dark: 1>
        FollowPalette: typing.ClassVar[ads.CDockManager.ColorSchemeMode]  # value = <ColorSchemeMode.FollowPalette: 2>
        Light: typing.ClassVar[ads.CDockManager.ColorSchemeMode]  # value = <ColorSchemeMode.Light: 0>
    class eAutoHideFlag(enum.IntFlag):
        """
        An enumeration.
        """
        AutoHideButtonCheckable: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideButtonCheckable: 8>
        AutoHideButtonTogglesArea: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideButtonTogglesArea: 4>
        AutoHideCloseButtonCollapsesDock: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideCloseButtonCollapsesDock: 64>
        AutoHideCloseOnOutsideMouseClick: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideCloseOnOutsideMouseClick: 1024>
        AutoHideFeatureEnabled: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideFeatureEnabled: 1>
        AutoHideHasCloseButton: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideHasCloseButton: 128>
        AutoHideHasMinimizeButton: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideHasMinimizeButton: 256>
        AutoHideOpenOnDragHover: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideOpenOnDragHover: 512>
        AutoHideShowOnMouseOver: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideShowOnMouseOver: 32>
        AutoHideSideBarsIconOnly: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideSideBarsIconOnly: 16>
        DefaultAutoHideConfig: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.DefaultAutoHideConfig: 1283>
        DockAreaHasAutoHideButton: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.DockAreaHasAutoHideButton: 2>
    class eConfigFlag(enum.IntFlag):
        """
        An enumeration.
        """
        ActiveTabHasCloseButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.ActiveTabHasCloseButton: 1>
        AllTabsHaveCloseButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.AllTabsHaveCloseButton: 128>
        AlwaysShowTabs: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.AlwaysShowTabs: 8192>
        DefaultBaseConfig: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DefaultBaseConfig: 268746787>
        DefaultDockAreaButtons: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DefaultDockAreaButtons: 49154>
        DefaultNonOpaqueConfig: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DefaultNonOpaqueConfig: 268748835>
        DefaultOpaqueConfig: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DefaultOpaqueConfig: 268748843>
        DisableStylesheet: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DisableStylesheet: 2147483648>
        DisableTabTextEliding: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DisableTabTextEliding: 67108864>
        DockAreaCloseButtonClosesTab: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaCloseButtonClosesTab: 4>
        DockAreaDynamicTabsMenuButtonVisibility: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaDynamicTabsMenuButtonVisibility: 131072>
        DockAreaHasCloseButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaHasCloseButton: 2>
        DockAreaHasTabsMenuButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaHasTabsMenuButton: 32768>
        DockAreaHasUndockButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaHasUndockButton: 16384>
        DockAreaHideDisabledButtons: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaHideDisabledButtons: 65536>
        DoubleClickUndocksWidget: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DoubleClickUndocksWidget: 268435456>
        DragPreviewHasWindowFrame: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DragPreviewHasWindowFrame: 4096>
        DragPreviewIsDynamic: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DragPreviewIsDynamic: 1024>
        DragPreviewShowsContentPixmap: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DragPreviewShowsContentPixmap: 2048>
        EqualSplitOnInsertion: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.EqualSplitOnInsertion: 4194304>
        FloatingContainerForceNativeTitleBar: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FloatingContainerForceNativeTitleBar: 8388608>
        FloatingContainerForceQWidgetTitleBar: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FloatingContainerForceQWidgetTitleBar: 16777216>
        FloatingContainerHasWidgetIcon: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FloatingContainerHasWidgetIcon: 524288>
        FloatingContainerHasWidgetTitle: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FloatingContainerHasWidgetTitle: 262144>
        FocusHighlighting: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FocusHighlighting: 2097152>
        HideSingleCentralWidgetTitleBar: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.HideSingleCentralWidgetTitleBar: 1048576>
        MiddleMouseButtonClosesTab: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.MiddleMouseButtonClosesTab: 33554432>
        NonOpaqueWithWindowFrame: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.NonOpaqueWithWindowFrame: 268752931>
        OpaqueSplitterResize: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.OpaqueSplitterResize: 8>
        RetainTabSizeWhenCloseButtonHidden: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.RetainTabSizeWhenCloseButtonHidden: 256>
        ShowTabTextOnlyForActiveTab: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.ShowTabTextOnlyForActiveTab: 134217728>
        TabCloseButtonIsToolButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.TabCloseButtonIsToolButton: 64>
        TabsAtBottom: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.TabsAtBottom: 536870912>
        UseNativeWindows: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.UseNativeWindows: 1073741824>
        XmlAutoFormattingEnabled: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.XmlAutoFormattingEnabled: 16>
        XmlCompressionEnabled: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.XmlCompressionEnabled: 32>
    class eConfigParam(enum.IntFlag):
        """
        An enumeration.
        """
        AutoHideOpenOnDragHoverDelay_ms: typing.ClassVar[ads.CDockManager.eConfigParam]  # value = <eConfigParam.AutoHideOpenOnDragHoverDelay_ms: 0>
        ConfigParamCount: typing.ClassVar[ads.CDockManager.eConfigParam]  # value = <eConfigParam.ConfigParamCount: 1>
    class eViewMenuInsertionOrder(enum.IntEnum):
        """
        An enumeration.
        """
        MenuAlphabeticallySorted: typing.ClassVar[ads.CDockManager.eViewMenuInsertionOrder]  # value = <eViewMenuInsertionOrder.MenuAlphabeticallySorted: 1>
        MenuSortedByInsertion: typing.ClassVar[ads.CDockManager.eViewMenuInsertionOrder]  # value = <eViewMenuInsertionOrder.MenuSortedByInsertion: 0>
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockManager" inherits "ads::CDockContainerWidget":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def autoHideConfigFlags() -> ads.CDockManager.eAutoHideFlag:
        ...
    @staticmethod
    def configFlags() -> ads.CDockManager.eConfigFlag:
        ...
    @staticmethod
    def configParam(Param: ads.CDockManager.eConfigParam, Default: typing.Any) -> typing.Any:
        ...
    @staticmethod
    def dockAreaCreated(*args, **kwargs):
        ...
    @staticmethod
    def dockWidgetAboutToBeRemoved(*args, **kwargs):
        ...
    @staticmethod
    def dockWidgetAdded(*args, **kwargs):
        ...
    @staticmethod
    def dockWidgetRemoved(*args, **kwargs):
        ...
    @staticmethod
    def floatingContainersTitle() -> str:
        ...
    @staticmethod
    def floatingWidgetCreated(*args, **kwargs):
        ...
    @staticmethod
    def focusedDockWidgetChanged(*args, **kwargs):
        ...
    @staticmethod
    def iconProvider() -> ads.CIconProvider:
        ...
    @staticmethod
    def isApplicationPaletteDark() -> bool:
        ...
    @staticmethod
    def openingPerspective(*args, **kwargs):
        ...
    @staticmethod
    def perspectiveListChanged(*args, **kwargs):
        ...
    @staticmethod
    def perspectiveListLoaded(*args, **kwargs):
        ...
    @staticmethod
    def perspectiveOpened(*args, **kwargs):
        ...
    @staticmethod
    def perspectivesRemoved(*args, **kwargs):
        ...
    @staticmethod
    def restoringState(*args, **kwargs):
        ...
    @staticmethod
    def setAutoHideConfigFlag(Flag: ads.CDockManager.eAutoHideFlag, /, On: bool = True) -> None:
        ...
    @staticmethod
    def setAutoHideConfigFlags(Flags: ads.CDockManager.eAutoHideFlag) -> None:
        ...
    @staticmethod
    def setConfigFlag(Flag: ads.CDockManager.eConfigFlag, /, On: bool = True) -> None:
        ...
    @staticmethod
    def setConfigFlags(Flags: ads.CDockManager.eConfigFlag) -> None:
        ...
    @staticmethod
    def setConfigParam(Param: ads.CDockManager.eConfigParam, Value: typing.Any) -> None:
        ...
    @staticmethod
    def setFloatingContainersTitle(Title: str) -> None:
        ...
    @staticmethod
    def startDragDistance() -> int:
        ...
    @staticmethod
    def stateRestored(*args, **kwargs):
        ...
    @staticmethod
    def testAutoHideConfigFlag(Flag: ads.CDockManager.eAutoHideFlag) -> bool:
        ...
    @staticmethod
    def testConfigFlag(Flag: ads.CDockManager.eConfigFlag) -> bool:
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def addAutoHideDockWidget(self, Location: ads.SideBarLocation, Dockwidget: ads.CDockWidget) -> ads.CAutoHideDockContainer:
        ...
    def addAutoHideDockWidgetToContainer(self, Location: ads.SideBarLocation, Dockwidget: ads.CDockWidget, DockContainerWidget: ads.CDockContainerWidget) -> ads.CAutoHideDockContainer:
        ...
    def addDockWidget(self, area: ads.DockWidgetArea, Dockwidget: ads.CDockWidget, /, DockAreaWidget: PySide6QtAds.ads.CDockAreaWidget | None = None, Index: int = -1) -> ads.CDockAreaWidget:
        ...
    def addDockWidgetFloating(self, Dockwidget: ads.CDockWidget) -> ads.CFloatingDockContainer:
        ...
    def addDockWidgetTab(self, area: ads.DockWidgetArea, Dockwidget: ads.CDockWidget) -> ads.CDockAreaWidget:
        ...
    def addDockWidgetTabToArea(self, Dockwidget: ads.CDockWidget, DockAreaWidget: ads.CDockAreaWidget, /, Index: int = -1) -> ads.CDockAreaWidget:
        ...
    def addDockWidgetToContainer(self, area: ads.DockWidgetArea, Dockwidget: ads.CDockWidget, DockContainerWidget: ads.CDockContainerWidget) -> ads.CDockAreaWidget:
        ...
    def addPerspective(self, UniquePrespectiveName: str) -> None:
        ...
    def addToggleViewActionToMenu(self, ToggleViewAction: PySide6.QtGui.QAction, /, Group: str = '', GroupIcon: PySide6.QtGui.QIcon | PySide6.QtGui.QPixmap = ...) -> PySide6.QtGui.QAction:
        ...
    def centralWidget(self) -> ads.CDockWidget:
        ...
    def changeEvent(self, event: PySide6.QtCore.QEvent) -> None:
        ...
    def containerOverlay(self) -> ads.CDockOverlay:
        ...
    def createDockWidget(self, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> ads.CDockWidget:
        ...
    def dockAreaOverlay(self) -> ads.CDockOverlay:
        ...
    def dockContainers(self) -> list[ads.CDockContainerWidget]:
        ...
    def dockFocusController(self) -> ads.CDockFocusController:
        ...
    def dockWidgetToolBarIconSize(self, State: ads.CDockWidget.eState) -> PySide6.QtCore.QSize:
        ...
    def dockWidgetToolBarStyle(self, State: ads.CDockWidget.eState) -> PySide6.QtCore.Qt.ToolButtonStyle:
        ...
    def dockWidgetsMap(self) -> dict[str, ads.CDockWidget]:
        ...
    def endLeavingMinimizedState(self) -> None:
        ...
    def eventFilter(self, obj: PySide6.QtCore.QObject, e: PySide6.QtCore.QEvent) -> bool:
        ...
    def findDockWidget(self, ObjectName: str) -> ads.CDockWidget:
        ...
    def floatingWidgets(self) -> list[ads.CFloatingDockContainer]:
        ...
    def focusedDockWidget(self) -> ads.CDockWidget:
        ...
    def globallyLockedDockWidgetFeatures(self) -> ads.CDockWidget.DockWidgetFeature:
        ...
    def hideManagerAndFloatingWidgets(self) -> None:
        ...
    def isDesiredStylesheetDark(self) -> bool:
        ...
    def isLeavingMinimizedState(self) -> bool:
        ...
    def isRestoringState(self) -> bool:
        ...
    def loadPerspectives(self, Settings: PySide6.QtCore.QSettings) -> None:
        ...
    def lockDockWidgetFeaturesGlobally(self, /, Features: ads.CDockWidget.DockWidgetFeature = ...) -> None:
        ...
    def notifyFloatingWidgetDrop(self, FloatingWidget: ads.CFloatingDockContainer) -> None:
        ...
    def notifyWidgetOrAreaRelocation(self, RelocatedWidget: PySide6.QtWidgets.QWidget) -> None:
        ...
    def openPerspective(self, PerspectiveName: str) -> None:
        ...
    def perspectiveNames(self) -> list[str]:
        ...
    def raise_(self) -> None:
        ...
    def registerDockContainer(self, DockContainer: ads.CDockContainerWidget) -> None:
        ...
    def registerFloatingWidget(self, FloatingWidget: ads.CFloatingDockContainer) -> None:
        ...
    def removeDockContainer(self, DockContainer: ads.CDockContainerWidget) -> None:
        ...
    def removeDockWidget(self, Dockwidget: ads.CDockWidget) -> None:
        ...
    def removeFloatingWidget(self, FloatingWidget: ads.CFloatingDockContainer) -> None:
        ...
    def removePerspective(self, Name: str) -> None:
        ...
    def removePerspectives(self, Names: collections.abc.Sequence[str]) -> None:
        ...
    def restoreHiddenFloatingWidgets(self) -> None:
        ...
    def restoreState(self, state: PySide6.QtCore.QByteArray | bytes | bytearray | memoryview, /, version: int | None = None) -> bool:
        ...
    def savePerspectives(self, Settings: PySide6.QtCore.QSettings) -> None:
        ...
    def saveState(self, /, version: int | None = None) -> PySide6.QtCore.QByteArray:
        ...
    def setCentralWidget(self, widget: ads.CDockWidget) -> ads.CDockAreaWidget:
        ...
    def setColorSchemeMode(self, Mode: ads.CDockManager.ColorSchemeMode) -> None:
        ...
    def setComponentsFactory(self, Factory: ads.CDockComponentsFactory) -> None:
        ...
    def setDockWidgetFocused(self, DockWidget: ads.CDockWidget) -> None:
        ...
    def setDockWidgetToolBarIconSize(self, IconSize: PySide6.QtCore.QSize, State: ads.CDockWidget.eState) -> None:
        ...
    def setDockWidgetToolBarStyle(self, Style: PySide6.QtCore.Qt.ToolButtonStyle, State: ads.CDockWidget.eState) -> None:
        ...
    def setSplitterSizes(self, ContainedArea: ads.CDockAreaWidget, sizes: collections.abc.Sequence[int]) -> None:
        ...
    def setViewMenuInsertionOrder(self, Order: ads.CDockManager.eViewMenuInsertionOrder) -> None:
        ...
    def showEvent(self, event: PySide6.QtGui.QShowEvent) -> None:
        ...
    def splitterSizes(self, ContainedArea: ads.CDockAreaWidget) -> list[int]:
        ...
    def viewMenu(self) -> PySide6.QtWidgets.QMenu:
        ...
    def zOrderIndex(self) -> int:
        ...
class CDockOverlay(PySide6.QtWidgets.QFrame):
    """
    CDockOverlay(self, parent: PySide6.QtWidgets.QWidget, /, Mode: PySide6QtAds.ads.CDockOverlay.eMode = Instance(PySide6QtAds.ads.CDockOverlay.eMode.ModeDockAreaOverlay)) -> None
    """
    class eMode(enum.IntEnum):
        """
        An enumeration.
        """
        ModeContainerOverlay: typing.ClassVar[ads.CDockOverlay.eMode]  # value = <eMode.ModeContainerOverlay: 1>
        ModeDockAreaOverlay: typing.ClassVar[ads.CDockOverlay.eMode]  # value = <eMode.ModeDockAreaOverlay: 0>
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockOverlay" inherits "QFrame":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, parent: PySide6.QtWidgets.QWidget, /, Mode: PySide6QtAds.ads.CDockOverlay.eMode = Instance(PySide6QtAds.ads.CDockOverlay.eMode.ModeDockAreaOverlay)) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def allowedAreas(self) -> ads.DockWidgetArea:
        ...
    def dropAreaUnderCursor(self) -> ads.DockWidgetArea:
        """
        dropAreaUnderCursor(self, GlobalPos: PySide6.QtCore.QPoint, /) -> PySide6QtAds.ads.DockWidgetArea
        """
    def dropOverlayRect(self) -> PySide6.QtCore.QRect:
        ...
    def dropPreviewEnabled(self) -> bool:
        ...
    def enableDropPreview(self, Enable: bool) -> None:
        ...
    def event(self, e: PySide6.QtCore.QEvent) -> bool:
        ...
    def hideEvent(self, e: PySide6.QtGui.QHideEvent) -> None:
        ...
    def hideOverlay(self) -> None:
        ...
    def paintEvent(self, e: PySide6.QtGui.QPaintEvent) -> None:
        ...
    def setAllowedArea(self, area: ads.DockWidgetArea, Enable: bool) -> None:
        ...
    def setAllowedAreas(self, areas: ads.DockWidgetArea) -> None:
        ...
    def showEvent(self, e: PySide6.QtGui.QShowEvent) -> None:
        ...
    def showOverlay(self, target: PySide6.QtWidgets.QWidget) -> ads.DockWidgetArea:
        """
        showOverlay(self, target: PySide6.QtWidgets.QWidget, GlobalPos: PySide6.QtCore.QPoint, /) -> PySide6QtAds.ads.DockWidgetArea
        """
    def tabIndexUnderCursor(self) -> int:
        ...
    def visibleDropAreaUnderCursor(self) -> ads.DockWidgetArea:
        """
        visibleDropAreaUnderCursor(self, GlobalPos: PySide6.QtCore.QPoint, /) -> PySide6QtAds.ads.DockWidgetArea
        """
class CDockOverlayCross(PySide6.QtWidgets.QWidget):
    """
    CDockOverlayCross(self, overlay: PySide6QtAds.ads.CDockOverlay, /, *, iconColors: str | None = None, iconFrameColor: PySide6.QtGui.QColor | None = None, iconBackgroundColor: PySide6.QtGui.QColor | None = None, iconOverlayColor: PySide6.QtGui.QColor | None = None, iconArrowColor: PySide6.QtGui.QColor | None = None, iconShadowColor: PySide6.QtGui.QColor | None = None) -> None
    """
    class eIconColor(enum.IntEnum):
        """
        An enumeration.
        """
        ArrowColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.ArrowColor: 3>
        FrameColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.FrameColor: 0>
        OverlayColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.OverlayColor: 2>
        ShadowColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.ShadowColor: 4>
        WindowBackgroundColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.WindowBackgroundColor: 1>
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockOverlayCross" inherits "QWidget":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, overlay: PySide6QtAds.ads.CDockOverlay, /, *, iconColors: str | None = None, iconFrameColor: PySide6.QtGui.QColor | None = None, iconBackgroundColor: PySide6.QtGui.QColor | None = None, iconOverlayColor: PySide6.QtGui.QColor | None = None, iconArrowColor: PySide6.QtGui.QColor | None = None, iconShadowColor: PySide6.QtGui.QColor | None = None) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def cursorLocation(self) -> ads.DockWidgetArea:
        """
        cursorLocation(self, GlobalPos: PySide6.QtCore.QPoint, /) -> PySide6QtAds.ads.DockWidgetArea
        """
    def event(self, e: PySide6.QtCore.QEvent) -> bool:
        ...
    def iconColor(self) -> PySide6.QtGui.QColor:
        """
        iconColor(self, ColorIndex: PySide6QtAds.ads.CDockOverlayCross.eIconColor, /) -> PySide6.QtGui.QColor
        """
    def iconColors(self) -> str:
        ...
    def reset(self) -> None:
        ...
    def setAreaWidgets(self, widgets: dict[ads.DockWidgetArea, PySide6.QtWidgets.QWidget]) -> None:
        ...
    def setIconArrowColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
        ...
    def setIconBackgroundColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
        ...
    def setIconColor(self, ColorIndex: ads.CDockOverlayCross.eIconColor, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
        ...
    def setIconColors(self, Colors: str) -> None:
        ...
    def setIconFrameColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
        ...
    def setIconOverlayColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
        ...
    def setIconShadowColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
        ...
    def setupOverlayCross(self, Mode: ads.CDockOverlay.eMode) -> None:
        ...
    def showEvent(self, e: PySide6.QtGui.QShowEvent) -> None:
        ...
    def updateOverlayIcons(self) -> None:
        ...
    def updatePosition(self) -> None:
        ...
class CDockSplitter(PySide6.QtWidgets.QSplitter):
    """
    CDockSplitter(self, orientation: PySide6.QtCore.Qt.Orientation, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
    CDockSplitter(self, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockSplitter" inherits "QSplitter":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, orientation: PySide6.QtCore.Qt.Orientation, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        __init__(self, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def firstWidget(self) -> PySide6.QtWidgets.QWidget:
        ...
    def hasVisibleContent(self) -> bool:
        ...
    def isResizingWithContainer(self) -> bool:
        ...
    def lastWidget(self) -> PySide6.QtWidgets.QWidget:
        ...
class CDockWidget(PySide6.QtWidgets.QFrame):
    """
    CDockWidget(self, manager: PySide6QtAds.ads.CDockManager, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
    CDockWidget(self, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
    """
    class DockWidgetFeature(enum.IntFlag):
        """
        An enumeration.
        """
        AllDockWidgetFeatures: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.AllDockWidgetFeatures: 575>
        CustomCloseHandling: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.CustomCloseHandling: 16>
        DefaultDockWidgetFeatures: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DefaultDockWidgetFeatures: 551>
        DeleteContentOnClose: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DeleteContentOnClose: 256>
        DockWidgetAlwaysCloseAndDelete: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetAlwaysCloseAndDelete: 72>
        DockWidgetClosable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetClosable: 1>
        DockWidgetDeleteOnClose: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetDeleteOnClose: 8>
        DockWidgetFloatable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetFloatable: 4>
        DockWidgetFocusable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetFocusable: 32>
        DockWidgetForceCloseWithArea: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetForceCloseWithArea: 64>
        DockWidgetMovable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetMovable: 2>
        DockWidgetPinnable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetPinnable: 512>
        GloballyLockableFeatures: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.GloballyLockableFeatures: 519>
        NoDockWidgetFeatures: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.NoDockWidgetFeatures: 0>
        NoTab: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.NoTab: 128>
    class eInsertMode(enum.IntEnum):
        """
        An enumeration.
        """
        AutoScrollArea: typing.ClassVar[ads.CDockWidget.eInsertMode]  # value = <eInsertMode.AutoScrollArea: 0>
        ForceNoScrollArea: typing.ClassVar[ads.CDockWidget.eInsertMode]  # value = <eInsertMode.ForceNoScrollArea: 2>
        ForceScrollArea: typing.ClassVar[ads.CDockWidget.eInsertMode]  # value = <eInsertMode.ForceScrollArea: 1>
    class eMinimumSizeHintMode(enum.IntEnum):
        """
        An enumeration.
        """
        MinimumSizeHintFromContent: typing.ClassVar[ads.CDockWidget.eMinimumSizeHintMode]  # value = <eMinimumSizeHintMode.MinimumSizeHintFromContent: 1>
        MinimumSizeHintFromContentMinimumSize: typing.ClassVar[ads.CDockWidget.eMinimumSizeHintMode]  # value = <eMinimumSizeHintMode.MinimumSizeHintFromContentMinimumSize: 3>
        MinimumSizeHintFromDockWidget: typing.ClassVar[ads.CDockWidget.eMinimumSizeHintMode]  # value = <eMinimumSizeHintMode.MinimumSizeHintFromDockWidget: 0>
        MinimumSizeHintFromDockWidgetMinimumSize: typing.ClassVar[ads.CDockWidget.eMinimumSizeHintMode]  # value = <eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize: 2>
    class eState(enum.IntEnum):
        """
        An enumeration.
        """
        StateDocked: typing.ClassVar[ads.CDockWidget.eState]  # value = <eState.StateDocked: 1>
        StateFloating: typing.ClassVar[ads.CDockWidget.eState]  # value = <eState.StateFloating: 2>
        StateHidden: typing.ClassVar[ads.CDockWidget.eState]  # value = <eState.StateHidden: 0>
    class eToggleViewActionMode(enum.IntEnum):
        """
        An enumeration.
        """
        ActionModeShow: typing.ClassVar[ads.CDockWidget.eToggleViewActionMode]  # value = <eToggleViewActionMode.ActionModeShow: 1>
        ActionModeToggle: typing.ClassVar[ads.CDockWidget.eToggleViewActionMode]  # value = <eToggleViewActionMode.ActionModeToggle: 0>
    class eToolBarStyleSource(enum.IntEnum):
        """
        An enumeration.
        """
        ToolBarStyleFromDockManager: typing.ClassVar[ads.CDockWidget.eToolBarStyleSource]  # value = <eToolBarStyleSource.ToolBarStyleFromDockManager: 0>
        ToolBarStyleFromDockWidget: typing.ClassVar[ads.CDockWidget.eToolBarStyleSource]  # value = <eToolBarStyleSource.ToolBarStyleFromDockWidget: 1>
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockWidget" inherits "QFrame":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def closeRequested(*args, **kwargs):
        ...
    @staticmethod
    def closed(*args, **kwargs):
        ...
    @staticmethod
    def emitTopLevelEventForWidget(TopLevelDockWidget: ads.CDockWidget, Floating: bool) -> None:
        ...
    @staticmethod
    def featuresChanged(*args, **kwargs):
        ...
    @staticmethod
    def titleChanged(*args, **kwargs):
        ...
    @staticmethod
    def topLevelChanged(*args, **kwargs):
        ...
    @staticmethod
    def viewToggled(*args, **kwargs):
        ...
    @staticmethod
    def visibilityChanged(*args, **kwargs):
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, manager: PySide6QtAds.ads.CDockManager, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        __init__(self, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def autoHideDockContainer(self) -> ads.CAutoHideDockContainer:
        ...
    def autoHideLocation(self) -> ads.SideBarLocation:
        ...
    def closeDockWidget(self) -> None:
        ...
    def closeDockWidgetInternal(self, /, ForceClose: bool = False) -> bool:
        ...
    def createDefaultToolBar(self) -> PySide6.QtWidgets.QToolBar:
        ...
    def deleteDockWidget(self) -> None:
        ...
    def dockAreaWidget(self) -> ads.CDockAreaWidget:
        ...
    def dockContainer(self) -> ads.CDockContainerWidget:
        ...
    def dockManager(self) -> ads.CDockManager:
        ...
    def emitTopLevelChanged(self, Floating: bool) -> None:
        ...
    def event(self, e: PySide6.QtCore.QEvent) -> bool:
        ...
    def features(self) -> ads.CDockWidget.DockWidgetFeature:
        ...
    def flagAsUnassigned(self) -> None:
        ...
    def floatingDockContainer(self) -> ads.CFloatingDockContainer:
        ...
    def icon(self) -> PySide6.QtGui.QIcon:
        ...
    def isAutoHide(self) -> bool:
        ...
    def isCentralWidget(self) -> bool:
        ...
    def isClosed(self) -> bool:
        ...
    def isCurrentTab(self) -> bool:
        ...
    def isFloating(self) -> bool:
        ...
    def isFullScreen(self) -> bool:
        ...
    def isInFloatingContainer(self) -> bool:
        ...
    def isTabbed(self) -> bool:
        ...
    def minimumSizeHint(self) -> PySide6.QtCore.QSize:
        ...
    def minimumSizeHintMode(self) -> ads.CDockWidget.eMinimumSizeHintMode:
        ...
    def notifyFeaturesChanged(self) -> None:
        ...
    def preferredAutoHideSideBarLocation(self) -> ads.SideBarLocation:
        ...
    def raise_(self) -> None:
        ...
    def requestCloseDockWidget(self) -> None:
        ...
    def saveState(self, Stream: PySide6.QtCore.QXmlStreamWriter) -> None:
        ...
    def setAsCurrentTab(self) -> None:
        ...
    def setAutoHide(self, Enable: bool, /, Location: ads.SideBarLocation = ..., TabIndex: int = -1) -> None:
        ...
    def setClosedState(self, Closed: bool) -> None:
        ...
    def setDockArea(self, DockArea: ads.CDockAreaWidget) -> None:
        ...
    def setDockManager(self, DockManager: ads.CDockManager) -> None:
        ...
    def setFeature(self, flag: ads.CDockWidget.DockWidgetFeature, on: bool) -> None:
        ...
    def setFeatures(self, features: ads.CDockWidget.DockWidgetFeature) -> None:
        ...
    def setFloating(self) -> None:
        ...
    def setIcon(self, Icon: PySide6.QtGui.QIcon | PySide6.QtGui.QPixmap) -> None:
        ...
    def setMinimumSizeHintMode(self, Mode: ads.CDockWidget.eMinimumSizeHintMode) -> None:
        ...
    def setPreferredAutoHideSideBarLocation(self, Location: ads.SideBarLocation) -> None:
        ...
    def setSideTabWidget(self, SideTab: ads.CAutoHideTab) -> None:
        ...
    def setTabToolTip(self, text: str) -> None:
        ...
    def setTitleBarActions(self, actions: collections.abc.Sequence[PySide6.QtGui.QAction]) -> None:
        ...
    def setToggleViewAction(self, action: PySide6.QtGui.QAction) -> None:
        ...
    def setToggleViewActionChecked(self, Checked: bool) -> None:
        ...
    def setToggleViewActionMode(self, Mode: ads.CDockWidget.eToggleViewActionMode) -> None:
        ...
    def setToolBar(self, ToolBar: PySide6.QtWidgets.QToolBar) -> None:
        ...
    def setToolBarIconSize(self, IconSize: PySide6.QtCore.QSize, State: ads.CDockWidget.eState) -> None:
        ...
    def setToolBarStyle(self, Style: PySide6.QtCore.Qt.ToolButtonStyle, State: ads.CDockWidget.eState) -> None:
        ...
    def setToolBarStyleSource(self, Source: ads.CDockWidget.eToolBarStyleSource) -> None:
        ...
    def setWidget(self, widget: PySide6.QtWidgets.QWidget, /, InsertMode: ads.CDockWidget.eInsertMode = ...) -> None:
        ...
    def showFullScreen(self) -> None:
        ...
    def showNormal(self) -> None:
        ...
    def sideTabWidget(self) -> ads.CAutoHideTab:
        ...
    def tabWidget(self) -> ads.CDockWidgetTab:
        ...
    def takeWidget(self) -> PySide6.QtWidgets.QWidget:
        ...
    def titleBarActions(self) -> list[PySide6.QtGui.QAction]:
        ...
    def toggleAutoHide(self, /, Location: ads.SideBarLocation = ...) -> None:
        ...
    def toggleView(self, /, Open: bool = True) -> None:
        ...
    def toggleViewAction(self) -> PySide6.QtGui.QAction:
        ...
    def toggleViewInternal(self, Open: bool) -> None:
        ...
    def toolBar(self) -> PySide6.QtWidgets.QToolBar:
        ...
    def toolBarIconSize(self, State: ads.CDockWidget.eState) -> PySide6.QtCore.QSize:
        ...
    def toolBarStyle(self, State: ads.CDockWidget.eState) -> PySide6.QtCore.Qt.ToolButtonStyle:
        ...
    def toolBarStyleSource(self) -> ads.CDockWidget.eToolBarStyleSource:
        ...
    def widget(self) -> PySide6.QtWidgets.QWidget:
        ...
class CDockWidgetTab(PySide6.QtWidgets.QFrame):
    """
    CDockWidgetTab(self, DockWidget: PySide6QtAds.ads.CDockWidget, /, parent: PySide6.QtWidgets.QWidget | None = None, *, activeTab: bool | None = None, iconSize: PySide6.QtCore.QSize | None = None) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockWidgetTab" inherits "QFrame":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def activeTabChanged(*args, **kwargs):
        ...
    @staticmethod
    def clicked(*args, **kwargs):
        ...
    @staticmethod
    def closeOtherTabsRequested(*args, **kwargs):
        ...
    @staticmethod
    def closeRequested(*args, **kwargs):
        ...
    @staticmethod
    def elidedChanged(*args, **kwargs):
        ...
    @staticmethod
    def moved(*args, **kwargs):
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, DockWidget: PySide6QtAds.ads.CDockWidget, /, parent: PySide6.QtWidgets.QWidget | None = None, *, activeTab: bool | None = None, iconSize: PySide6.QtCore.QSize | None = None) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def buildContextMenu(self, arg__1: PySide6.QtWidgets.QMenu) -> PySide6.QtWidgets.QMenu:
        ...
    def contextMenuEvent(self, ev: PySide6.QtGui.QContextMenuEvent) -> None:
        ...
    def dockAreaWidget(self) -> ads.CDockAreaWidget:
        ...
    def dockWidget(self) -> ads.CDockWidget:
        ...
    def dragState(self) -> ads.eDragState:
        ...
    def event(self, e: PySide6.QtCore.QEvent) -> bool:
        ...
    def icon(self) -> PySide6.QtGui.QIcon:
        ...
    def iconSize(self) -> PySide6.QtCore.QSize:
        ...
    def isActiveTab(self) -> bool:
        ...
    def isClosable(self) -> bool:
        ...
    def isTitleElided(self) -> bool:
        ...
    def mouseDoubleClickEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def mouseMoveEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def mousePressEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def mouseReleaseEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def setActiveTab(self, active: bool) -> None:
        ...
    def setDockAreaWidget(self, DockArea: ads.CDockAreaWidget) -> None:
        ...
    def setElideMode(self, mode: PySide6.QtCore.Qt.TextElideMode) -> None:
        ...
    def setIcon(self, Icon: PySide6.QtGui.QIcon | PySide6.QtGui.QPixmap) -> None:
        ...
    def setIconSize(self, Size: PySide6.QtCore.QSize) -> None:
        ...
    def setText(self, title: str) -> None:
        ...
    def setVisible(self, visible: bool) -> None:
        ...
    def text(self) -> str:
        ...
    def updateStyle(self) -> None:
        ...
class CDockingStateReader(PySide6.QtCore.QXmlStreamReader):
    """
    CDockingStateReader(self, /) -> None
    """
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def fileVersion(self) -> int:
        ...
    def setFileVersion(self, FileVersion: int) -> None:
        ...
class CElidingLabel(PySide6.QtWidgets.QLabel):
    """
    CElidingLabel(self, text: str, /, parent: PySide6.QtWidgets.QWidget | None = None, f: PySide6.QtCore.Qt.WindowType = Default(Qt.WindowFlags )) -> None
    CElidingLabel(self, /, parent: PySide6.QtWidgets.QWidget | None = None, f: PySide6.QtCore.Qt.WindowType = Default(Qt.WindowFlags )) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CElidingLabel" inherits "QLabel":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def clicked(*args, **kwargs):
        ...
    @staticmethod
    def doubleClicked(*args, **kwargs):
        ...
    @staticmethod
    def elidedChanged(*args, **kwargs):
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, text: str, /, parent: PySide6.QtWidgets.QWidget | None = None, f: PySide6.QtCore.Qt.WindowType = Default(Qt.WindowFlags )) -> None
        __init__(self, /, parent: PySide6.QtWidgets.QWidget | None = None, f: PySide6.QtCore.Qt.WindowType = Default(Qt.WindowFlags )) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def elideMode(self) -> PySide6.QtCore.Qt.TextElideMode:
        ...
    def isElided(self) -> bool:
        ...
    def minimumSizeHint(self) -> PySide6.QtCore.QSize:
        ...
    def mouseDoubleClickEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def mouseReleaseEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
        ...
    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
        ...
    def setElideMode(self, mode: PySide6.QtCore.Qt.TextElideMode) -> None:
        ...
    def setText(self, text: str) -> None:
        ...
    def sizeHint(self) -> PySide6.QtCore.QSize:
        ...
    def text(self) -> str:
        ...
class CFloatingDockContainer(PySide6.QtWidgets.QDockWidget, ads.IFloatingWidget):
    """
    CFloatingDockContainer(self, DockManager: PySide6QtAds.ads.CDockManager, /) -> None
    CFloatingDockContainer(self, DockArea: PySide6QtAds.ads.CDockAreaWidget, /) -> None
    CFloatingDockContainer(self, DockWidget: PySide6QtAds.ads.CDockWidget, /) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CFloatingDockContainer" inherits "QDockWidget":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def startPlatformDrag(FloatingWidget: ads.CFloatingDockContainer, GlobalPressPos: PySide6.QtCore.QPoint, DragSource: PySide6.QtWidgets.QWidget, /, DragOffset: PySide6.QtCore.QPoint | None = None) -> PySide6.QtCore.Qt.DropAction:
        ...
    @staticmethod
    def waylandMoveOrLeaveInWindowPreview(Preview: ads.CFloatingDragPreview, SourceWindow: PySide6.QtWidgets.QWidget, GlobalPos: PySide6.QtCore.QPoint) -> bool:
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, DockManager: PySide6QtAds.ads.CDockManager, /) -> None
        __init__(self, DockArea: PySide6QtAds.ads.CDockAreaWidget, /) -> None
        __init__(self, DockWidget: PySide6QtAds.ads.CDockWidget, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def changeEvent(self, event: PySide6.QtCore.QEvent) -> None:
        ...
    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        ...
    def deleteContent(self) -> None:
        ...
    def dockContainer(self) -> ads.CDockContainerWidget:
        ...
    def dockWidgets(self) -> list[ads.CDockWidget]:
        ...
    def event(self, e: PySide6.QtCore.QEvent) -> bool:
        ...
    def finishDragging(self) -> None:
        ...
    def finishDropOperation(self) -> None:
        ...
    def hasNativeTitleBar(self) -> bool:
        ...
    def hasTopLevelDockWidget(self) -> bool:
        ...
    def hideEvent(self, event: PySide6.QtGui.QHideEvent) -> None:
        ...
    def initFloatingGeometry(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize) -> None:
        ...
    def isClosable(self) -> bool:
        ...
    def isDraggingActive(self) -> bool:
        ...
    def isMaximized(self) -> bool:
        ...
    def moveEvent(self, event: PySide6.QtGui.QMoveEvent) -> None:
        ...
    def moveFloating(self) -> None:
        ...
    def onMaximizeRequest(self) -> None:
        ...
    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
        ...
    def show(self) -> None:
        ...
    def showEvent(self, event: PySide6.QtGui.QShowEvent) -> None:
        ...
    def showMaximized(self) -> None:
        ...
    def showNormal(self, /, fixGeometry: bool = False) -> None:
        ...
    def startDragging(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize, MouseEventHandler: PySide6.QtWidgets.QWidget) -> None:
        ...
    def startFloating(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize, DragState: ads.eDragState, MouseEventHandler: PySide6.QtWidgets.QWidget) -> None:
        ...
    def topLevelDockWidget(self) -> ads.CDockWidget:
        ...
    def updateWindowTitle(self) -> None:
        ...
    def windowHandle(self) -> PySide6.QtGui.QWindow:
        ...
class CFloatingDragPreview(PySide6.QtWidgets.QWidget, ads.IFloatingWidget):
    """
    CFloatingDragPreview(self, Content: PySide6QtAds.ads.CDockAreaWidget, /) -> None
    CFloatingDragPreview(self, Content: PySide6QtAds.ads.CDockWidget, /) -> None
    CFloatingDragPreview(self, Content: PySide6.QtWidgets.QWidget, parent: PySide6.QtWidgets.QWidget, /) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CFloatingDragPreview" inherits "QWidget":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    @staticmethod
    def draggingCanceled(*args, **kwargs):
        ...
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, Content: PySide6QtAds.ads.CDockAreaWidget, /) -> None
        __init__(self, Content: PySide6QtAds.ads.CDockWidget, /) -> None
        __init__(self, Content: PySide6.QtWidgets.QWidget, parent: PySide6.QtWidgets.QWidget, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def cancelDraggingSilently(self) -> None:
        ...
    def cleanupAutoHideContainerWidget(self, ContainerDropArea: ads.DockWidgetArea) -> None:
        ...
    def eventFilter(self, watched: PySide6.QtCore.QObject, event: PySide6.QtCore.QEvent) -> bool:
        ...
    def finishDragging(self) -> None:
        ...
    def moveFloating(self) -> None:
        """
        moveFloating(self, GlobalPos: PySide6.QtCore.QPoint, /) -> None
        """
    def paintEvent(self, e: PySide6.QtGui.QPaintEvent) -> None:
        ...
    def setSourceContainer(self, Container: ads.CDockContainerWidget) -> None:
        ...
    def startFloating(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize, DragState: ads.eDragState, MouseEventHandler: PySide6.QtWidgets.QWidget) -> None:
        ...
class CIconProvider(Shiboken.Object):
    """
    CIconProvider(self, /) -> None
    """
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def customIcon(self, IconId: ads.eIcon) -> PySide6.QtGui.QIcon:
        ...
    def registerCustomIcon(self, IconId: ads.eIcon, icon: PySide6.QtGui.QIcon | PySide6.QtGui.QPixmap) -> None:
        ...
class CSpacerWidget(PySide6.QtWidgets.QWidget):
    """
    CSpacerWidget(self, /, Parent: PySide6.QtWidgets.QWidget | None = None) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CSpacerWidget" inherits "QWidget":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, /, Parent: PySide6.QtWidgets.QWidget | None = None) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def minimumSizeHint(self) -> PySide6.QtCore.QSize:
        ...
    def sizeHint(self) -> PySide6.QtCore.QSize:
        ...
class CTitleBarButton(PySide6.QtWidgets.QToolButton):
    """
    CTitleBarButton(self, ShowInTitleBar: bool, HideWhenDisabled: bool, ButtonId: PySide6QtAds.ads.TitleBarButton, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
    """
    staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CTitleBarButton" inherits "QToolButton":...
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, ShowInTitleBar: bool, HideWhenDisabled: bool, ButtonId: PySide6QtAds.ads.TitleBarButton, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def buttonId(self) -> ads.TitleBarButton:
        ...
    def event(self, ev: PySide6.QtCore.QEvent) -> bool:
        ...
    def isInAutoHideArea(self) -> bool:
        ...
    def setShowInTitleBar(self, Show: bool) -> None:
        ...
    def setVisible(self, visible: bool) -> None:
        ...
    def titleBar(self) -> ads.CDockAreaTitleBar:
        ...
class DockWidgetArea(enum.IntFlag):
    """
    An enumeration.
    """
    AllDockAreas: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.AllDockAreas: 31>
    AutoHideDockAreas: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.AutoHideDockAreas: 480>
    BottomAutoHideArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.BottomAutoHideArea: 256>
    BottomDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.BottomDockWidgetArea: 8>
    CenterDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.CenterDockWidgetArea: 16>
    LeftAutoHideArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.LeftAutoHideArea: 32>
    LeftDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.LeftDockWidgetArea: 1>
    NoDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.NoDockWidgetArea: 0>
    OuterDockAreas: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.OuterDockAreas: 15>
    RightAutoHideArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.RightAutoHideArea: 64>
    RightDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.RightDockWidgetArea: 2>
    TopAutoHideArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.TopAutoHideArea: 128>
    TopDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.TopDockWidgetArea: 4>
class IFloatingWidget(Shiboken.Object):
    """
    IFloatingWidget(self, /) -> None
    """
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
    def __delattr__(self, name):
        """
        Implement delattr(self, name).
        """
    def __init__(self, *args, **kwargs):
        """
        __init__(self, /) -> None
        
        Initialize self.  See help(type(self)) for accurate signature.
        """
    def __setattr__(self, name, value):
        """
        Implement setattr(self, name, value).
        """
    def finishDragging(self) -> None:
        ...
    def moveFloating(self) -> None:
        ...
    def startFloating(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize, DragState: ads.eDragState, MouseEventHandler: PySide6.QtWidgets.QWidget) -> None:
        ...
class ads(Shiboken.Object):
    class CAutoHideDockContainer(PySide6.QtWidgets.QFrame):
        """
        CAutoHideDockContainer(self, DockWidget: PySide6QtAds.ads.CDockWidget, area: PySide6QtAds.ads.SideBarLocation, parent: PySide6QtAds.ads.CDockContainerWidget, /, *, sideBarLocation: int | None = None) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CAutoHideDockContainer" inherits "QFrame":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, DockWidget: PySide6QtAds.ads.CDockWidget, area: PySide6QtAds.ads.SideBarLocation, parent: PySide6QtAds.ads.CDockContainerWidget, /, *, sideBarLocation: int | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def addDockWidget(self, DockWidget: ads.CDockWidget) -> None:
            ...
        def autoHideSideBar(self) -> ads.CAutoHideSideBar:
            ...
        def autoHideTab(self) -> ads.CAutoHideTab:
            ...
        def cleanupAndDelete(self) -> None:
            ...
        def collapseView(self, Enable: bool) -> None:
            ...
        def dockAreaWidget(self) -> ads.CDockAreaWidget:
            ...
        def dockContainer(self) -> ads.CDockContainerWidget:
            ...
        def dockWidget(self) -> ads.CDockWidget:
            ...
        def dragLeaveEvent(self, ev: PySide6.QtGui.QDragLeaveEvent) -> None:
            ...
        def event(self, event: PySide6.QtCore.QEvent) -> bool:
            ...
        def eventFilter(self, watched: PySide6.QtCore.QObject, event: PySide6.QtCore.QEvent) -> bool:
            ...
        def leaveEvent(self, event: PySide6.QtCore.QEvent) -> None:
            ...
        def moveContentsToParent(self) -> None:
            ...
        def moveToNewSideBarLocation(self, SideBarLocation: ads.SideBarLocation, /, TabIndex: int = -1) -> None:
            ...
        def orientation(self) -> PySide6.QtCore.Qt.Orientation:
            ...
        def resetToInitialDockWidgetSize(self) -> None:
            ...
        def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
            ...
        def saveState(self, Stream: PySide6.QtCore.QXmlStreamWriter) -> None:
            ...
        def setSideBarLocation(self, SideBarLocation: ads.SideBarLocation) -> None:
            ...
        def setSize(self, Size: int) -> None:
            ...
        def sideBarLocation(self) -> ads.SideBarLocation:
            ...
        def tabIndex(self) -> int:
            ...
        def toggleCollapseState(self) -> None:
            ...
        def toggleView(self, Enable: bool) -> None:
            ...
        def updateSize(self) -> None:
            ...
    class CAutoHideSideBar(PySide6.QtWidgets.QScrollArea):
        """
        CAutoHideSideBar(self, parent: PySide6QtAds.ads.CDockContainerWidget, area: PySide6QtAds.ads.SideBarLocation, /, *, sideBarLocation: int | None = None, orientation: PySide6.QtCore.Qt.Orientation | None = None, spacing: int | None = None) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CAutoHideSideBar" inherits "QScrollArea":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, parent: PySide6QtAds.ads.CDockContainerWidget, area: PySide6QtAds.ads.SideBarLocation, /, *, sideBarLocation: int | None = None, orientation: PySide6.QtCore.Qt.Orientation | None = None, spacing: int | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def addAutoHideWidget(self, AutoHideWidget: ads.CAutoHideDockContainer, /, Index: int = 'ads.eTabIndex.TabDefaultInsertIndex') -> None:
            ...
        def count(self) -> int:
            ...
        def dockContainer(self) -> ads.CDockContainerWidget:
            ...
        def eventFilter(self, watched: PySide6.QtCore.QObject, event: PySide6.QtCore.QEvent) -> bool:
            ...
        def hasVisibleTabs(self) -> bool:
            ...
        def indexOfTab(self, Tab: ads.CAutoHideTab) -> int:
            ...
        def insertDockWidget(self, Index: int, DockWidget: ads.CDockWidget) -> ads.CAutoHideDockContainer:
            ...
        def insertTab(self, Index: int, SideTab: ads.CAutoHideTab) -> None:
            ...
        def minimumSizeHint(self) -> PySide6.QtCore.QSize:
            ...
        def orientation(self) -> PySide6.QtCore.Qt.Orientation:
            ...
        def removeAutoHideWidget(self, AutoHideWidget: ads.CAutoHideDockContainer) -> None:
            ...
        def removeTab(self, SideTab: ads.CAutoHideTab) -> None:
            ...
        def saveState(self, Stream: PySide6.QtCore.QXmlStreamWriter) -> None:
            ...
        def setSpacing(self, Spacing: int) -> None:
            ...
        def sideBarLocation(self) -> ads.SideBarLocation:
            ...
        def sizeHint(self) -> PySide6.QtCore.QSize:
            ...
        def spacing(self) -> int:
            ...
        def tab(self, index: int) -> ads.CAutoHideTab:
            ...
        def tabAt(self, Pos: PySide6.QtCore.QPoint) -> int:
            ...
        def tabInsertIndexAt(self, Pos: PySide6.QtCore.QPoint) -> int:
            ...
        def visibleTabCount(self) -> int:
            ...
    class CAutoHideTab(ads.CPushButton):
        """
        CAutoHideTab(self, /, parent: PySide6.QtWidgets.QWidget | None = None, *, sideBarLocation: int | None = None, orientation: PySide6.QtCore.Qt.Orientation | None = None, activeTab: bool | None = None, iconOnly: bool | None = None) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CAutoHideTab" inherits "ads::CPushButton":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, /, parent: PySide6.QtWidgets.QWidget | None = None, *, sideBarLocation: int | None = None, orientation: PySide6.QtCore.Qt.Orientation | None = None, activeTab: bool | None = None, iconOnly: bool | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def contextMenuEvent(self, ev: PySide6.QtGui.QContextMenuEvent) -> None:
            ...
        def dockWidget(self) -> ads.CDockWidget:
            ...
        def dragEnterEvent(self, ev: PySide6.QtGui.QDragEnterEvent) -> None:
            ...
        def dragLeaveEvent(self, ev: PySide6.QtGui.QDragLeaveEvent) -> None:
            ...
        def event(self, event: PySide6.QtCore.QEvent) -> bool:
            ...
        def iconOnly(self) -> bool:
            ...
        def isActiveTab(self) -> bool:
            ...
        def mouseMoveEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mousePressEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mouseReleaseEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def orientation(self) -> PySide6.QtCore.Qt.Orientation:
            ...
        def removeFromSideBar(self) -> None:
            ...
        def requestCloseDockWidget(self) -> None:
            ...
        def setDockWidget(self, DockWidget: ads.CDockWidget) -> None:
            ...
        def setDockWidgetFloating(self) -> None:
            ...
        def setOrientation(self, Orientation: PySide6.QtCore.Qt.Orientation) -> None:
            ...
        def setSideBar(self, SideTabBar: ads.CAutoHideSideBar) -> None:
            ...
        def sideBar(self) -> ads.CAutoHideSideBar:
            ...
        def sideBarLocation(self) -> ads.SideBarLocation:
            ...
        def tabIndex(self) -> int:
            ...
        def unpinDockWidget(self) -> None:
            ...
        def updateStyle(self) -> None:
            ...
    class CDockAreaTabBar(PySide6.QtWidgets.QScrollArea):
        """
        CDockAreaTabBar(self, parent: PySide6QtAds.ads.CDockAreaWidget, /) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockAreaTabBar" inherits "QScrollArea":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def currentChanged(*args, **kwargs):
            ...
        @staticmethod
        def currentChanging(*args, **kwargs):
            ...
        @staticmethod
        def elidedChanged(*args, **kwargs):
            ...
        @staticmethod
        def removingTab(*args, **kwargs):
            ...
        @staticmethod
        def tabBarClicked(*args, **kwargs):
            ...
        @staticmethod
        def tabCloseRequested(*args, **kwargs):
            ...
        @staticmethod
        def tabClosed(*args, **kwargs):
            ...
        @staticmethod
        def tabInserted(*args, **kwargs):
            ...
        @staticmethod
        def tabMoved(*args, **kwargs):
            ...
        @staticmethod
        def tabOpened(*args, **kwargs):
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, parent: PySide6QtAds.ads.CDockAreaWidget, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def areTabsOverflowing(self) -> bool:
            ...
        def closeTab(self, Index: int) -> None:
            ...
        def count(self) -> int:
            ...
        def currentIndex(self) -> int:
            ...
        def currentTab(self) -> ads.CDockWidgetTab:
            ...
        def eventFilter(self, watched: PySide6.QtCore.QObject, event: PySide6.QtCore.QEvent) -> bool:
            ...
        def insertTab(self, Index: int, Tab: ads.CDockWidgetTab) -> None:
            ...
        def isTabOpen(self, Index: int) -> bool:
            ...
        def minimumSizeHint(self) -> PySide6.QtCore.QSize:
            ...
        def removeTab(self, Tab: ads.CDockWidgetTab) -> None:
            ...
        def setCurrentIndex(self, Index: int) -> None:
            ...
        def sizeHint(self) -> PySide6.QtCore.QSize:
            ...
        def tab(self, Index: int) -> ads.CDockWidgetTab:
            ...
        def tabAt(self, Pos: PySide6.QtCore.QPoint) -> int:
            ...
        def tabInsertIndexAt(self, Pos: PySide6.QtCore.QPoint) -> int:
            ...
        def wheelEvent(self, Event: PySide6.QtGui.QWheelEvent) -> None:
            ...
    class CDockAreaTitleBar(PySide6.QtWidgets.QFrame):
        """
        CDockAreaTitleBar(self, parent: PySide6QtAds.ads.CDockAreaWidget, /) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockAreaTitleBar" inherits "QFrame":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def tabBarClicked(*args, **kwargs):
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, parent: PySide6QtAds.ads.CDockAreaWidget, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def autoHideTitleLabel(self) -> ads.CElidingLabel:
            ...
        def buildContextMenu(self, arg__1: PySide6.QtWidgets.QMenu) -> PySide6.QtWidgets.QMenu:
            ...
        def button(self, which: ads.TitleBarButton) -> ads.CTitleBarButton:
            ...
        def contextMenuEvent(self, event: PySide6.QtGui.QContextMenuEvent) -> None:
            ...
        def dockAreaWidget(self) -> ads.CDockAreaWidget:
            ...
        def indexOf(self, widget: PySide6.QtWidgets.QWidget) -> int:
            ...
        def insertWidget(self, index: int, widget: PySide6.QtWidgets.QWidget) -> None:
            ...
        def isAutoHide(self) -> bool:
            ...
        def markTabsMenuOutdated(self) -> None:
            ...
        def mouseDoubleClickEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mouseMoveEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mousePressEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mouseReleaseEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
            ...
        def setAreaFloating(self) -> None:
            ...
        def setVisible(self, Visible: bool) -> None:
            ...
        def showAutoHideControls(self, Show: bool) -> None:
            ...
        def tabBar(self) -> ads.CDockAreaTabBar:
            ...
        def titleBarButtonToolTip(self, Button: ads.TitleBarButton) -> str:
            ...
        def updateDockWidgetActionsButtons(self) -> None:
            ...
    class CDockAreaWidget(PySide6.QtWidgets.QFrame):
        """
        CDockAreaWidget(self, DockManager: PySide6QtAds.ads.CDockManager, parent: PySide6QtAds.ads.CDockContainerWidget, /) -> None
        """
        class eDockAreaFlag(enum.IntFlag):
            """
            An enumeration.
            """
            DefaultFlags: typing.ClassVar[ads.CDockAreaWidget.eDockAreaFlag]  # value = <eDockAreaFlag.DefaultFlags: 0>
            HideSingleWidgetTitleBar: typing.ClassVar[ads.CDockAreaWidget.eDockAreaFlag]  # value = <eDockAreaFlag.HideSingleWidgetTitleBar: 1>
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockAreaWidget" inherits "QFrame":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def currentChanged(*args, **kwargs):
            ...
        @staticmethod
        def currentChanging(*args, **kwargs):
            ...
        @staticmethod
        def tabBarClicked(*args, **kwargs):
            ...
        @staticmethod
        def viewToggled(*args, **kwargs):
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, DockManager: PySide6QtAds.ads.CDockManager, parent: PySide6QtAds.ads.CDockContainerWidget, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def addDockWidget(self, DockWidget: ads.CDockWidget) -> None:
            ...
        def allowedAreas(self) -> ads.DockWidgetArea:
            ...
        def autoHideDockContainer(self) -> ads.CAutoHideDockContainer:
            ...
        def closeArea(self) -> None:
            ...
        def closeOtherAreas(self) -> None:
            ...
        def containsCentralWidget(self) -> bool:
            ...
        def contentAreaGeometry(self) -> PySide6.QtCore.QRect:
            ...
        def currentDockWidget(self) -> ads.CDockWidget:
            ...
        def currentIndex(self) -> int:
            ...
        def dockAreaFlags(self) -> ads.CDockAreaWidget.eDockAreaFlag:
            ...
        def dockContainer(self) -> ads.CDockContainerWidget:
            ...
        def dockManager(self) -> ads.CDockManager:
            ...
        def dockWidget(self, Index: int) -> ads.CDockWidget:
            ...
        def dockWidgets(self) -> list[ads.CDockWidget]:
            ...
        def dockWidgetsCount(self) -> int:
            ...
        def features(self, /, Mode: ads.eBitwiseOperator = ...) -> ads.CDockWidget.DockWidgetFeature:
            ...
        def hideAreaWithNoVisibleContent(self) -> None:
            ...
        def index(self, DockWidget: ads.CDockWidget) -> int:
            ...
        def indexOfFirstOpenDockWidget(self) -> int:
            ...
        def insertDockWidget(self, index: int, DockWidget: ads.CDockWidget, /, Activate: bool = True) -> None:
            ...
        def internalSetCurrentDockWidget(self, DockWidget: ads.CDockWidget) -> None:
            ...
        def isAutoHide(self) -> bool:
            ...
        def isCentralWidgetArea(self) -> bool:
            ...
        def isTopLevelArea(self) -> bool:
            ...
        def markTitleBarMenuOutdated(self) -> None:
            ...
        def minimumSizeHint(self) -> PySide6.QtCore.QSize:
            ...
        def nextOpenDockWidget(self, DockWidget: ads.CDockWidget) -> ads.CDockWidget:
            ...
        def openDockWidgetsCount(self) -> int:
            ...
        def openedDockWidgets(self) -> list[ads.CDockWidget]:
            ...
        def parentSplitter(self) -> ads.CDockSplitter:
            ...
        def removeDockWidget(self, DockWidget: ads.CDockWidget) -> None:
            ...
        def saveState(self, Stream: PySide6.QtCore.QXmlStreamWriter) -> None:
            ...
        def setAllowedAreas(self, areas: ads.DockWidgetArea) -> None:
            ...
        def setAutoHide(self, Enable: bool, /, Location: ads.SideBarLocation = ..., TabIndex: int = -1) -> None:
            ...
        def setAutoHideDockContainer(self, AutoHideDockContainer: ads.CAutoHideDockContainer) -> None:
            ...
        def setCurrentDockWidget(self, DockWidget: ads.CDockWidget) -> None:
            ...
        def setCurrentIndex(self, index: int) -> None:
            ...
        def setDockAreaFlag(self, Flag: ads.CDockAreaWidget.eDockAreaFlag, On: bool) -> None:
            ...
        def setDockAreaFlags(self, Flags: ads.CDockAreaWidget.eDockAreaFlag) -> None:
            ...
        def setFloating(self) -> None:
            ...
        def setVisible(self, Visible: bool) -> None:
            ...
        def titleBar(self) -> ads.CDockAreaTitleBar:
            ...
        def titleBarButton(self, which: ads.TitleBarButton) -> PySide6.QtWidgets.QAbstractButton:
            ...
        def titleBarGeometry(self) -> PySide6.QtCore.QRect:
            ...
        def toggleAutoHide(self, /, Location: ads.SideBarLocation = ...) -> None:
            ...
        def toggleDockWidgetView(self, DockWidget: ads.CDockWidget, Open: bool) -> None:
            ...
        def toggleView(self, Open: bool) -> None:
            ...
        def updateTitleBarButtonVisibility(self, IsTopLevel: bool) -> None:
            ...
        def updateTitleBarVisibility(self) -> None:
            ...
        def updateWindowTitle(self) -> None:
            ...
    class CDockComponentsFactory(Shiboken.Object):
        """
        CDockComponentsFactory(self, /) -> None
        """
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def resetDefaultFactory() -> None:
            ...
        @staticmethod
        def setFactory(Factory: ads.CDockComponentsFactory) -> None:
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def createDockAreaTabBar(self, DockArea: ads.CDockAreaWidget) -> ads.CDockAreaTabBar:
            ...
        def createDockAreaTitleBar(self, DockArea: ads.CDockAreaWidget) -> ads.CDockAreaTitleBar:
            ...
        def createDockWidgetSideTab(self, DockWidget: ads.CDockWidget) -> ads.CAutoHideTab:
            ...
        def createDockWidgetTab(self, DockWidget: ads.CDockWidget) -> ads.CDockWidgetTab:
            ...
    class CDockContainerWidget(PySide6.QtWidgets.QFrame):
        """
        CDockContainerWidget(self, DockManager: PySide6QtAds.ads.CDockManager, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockContainerWidget" inherits "QFrame":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def autoHideWidgetCreated(*args, **kwargs):
            ...
        @staticmethod
        def dockAreaViewToggled(*args, **kwargs):
            ...
        @staticmethod
        def dockAreasAdded(*args, **kwargs):
            ...
        @staticmethod
        def dockAreasRemoved(*args, **kwargs):
            ...
        @staticmethod
        def floatingWidgetFromDropEvent(e: PySide6.QtGui.QDropEvent, DockManager: ads.CDockManager) -> ads.CFloatingDockContainer:
            ...
        @staticmethod
        def showDropOverlays(DockManager: ads.CDockManager, TopContainer: ads.CDockContainerWidget, GlobalPos: PySide6.QtCore.QPoint, ContentPinnable: bool) -> None:
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, DockManager: PySide6QtAds.ads.CDockManager, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def addDockArea(self, DockAreaWidget: ads.CDockAreaWidget, /, area: ads.DockWidgetArea = ...) -> None:
            ...
        def addDockWidget(self, area: ads.DockWidgetArea, Dockwidget: ads.CDockWidget, /, DockAreaWidget: PySide6QtAds.ads.CDockAreaWidget | None = None, Index: int = -1) -> ads.CDockAreaWidget:
            ...
        def autoHideSideBar(self, area: ads.SideBarLocation) -> ads.CAutoHideSideBar:
            ...
        def autoHideWidgets(self) -> list[ads.CAutoHideDockContainer]:
            ...
        def closeOtherAreas(self, KeepOpenArea: ads.CDockAreaWidget) -> None:
            ...
        def contentRect(self) -> PySide6.QtCore.QRect:
            ...
        def contentRectGlobal(self) -> PySide6.QtCore.QRect:
            ...
        def createAndSetupAutoHideContainer(self, area: ads.SideBarLocation, DockWidget: ads.CDockWidget, /, TabIndex: int = -1) -> ads.CAutoHideDockContainer:
            ...
        def createRootSplitter(self) -> None:
            ...
        def createSideTabBarWidgets(self) -> None:
            ...
        def dockArea(self, Index: int) -> ads.CDockAreaWidget:
            ...
        def dockAreaAt(self, GlobalPos: PySide6.QtCore.QPoint) -> ads.CDockAreaWidget:
            ...
        def dockAreaCount(self) -> int:
            ...
        def dockManager(self) -> ads.CDockManager:
            ...
        def dockWidgets(self) -> list[ads.CDockWidget]:
            ...
        def dragEnterEvent(self, e: PySide6.QtGui.QDragEnterEvent) -> None:
            ...
        def dragLeaveEvent(self, e: PySide6.QtGui.QDragLeaveEvent) -> None:
            ...
        def dragMoveEvent(self, e: PySide6.QtGui.QDragMoveEvent) -> None:
            ...
        def dropEvent(self, e: PySide6.QtGui.QDropEvent) -> None:
            ...
        def dropFloatingWidget(self, FloatingWidget: ads.CFloatingDockContainer, TargetPos: PySide6.QtCore.QPoint) -> None:
            ...
        def dropWidget(self, Widget: PySide6.QtWidgets.QWidget, DropArea: ads.DockWidgetArea, TargetAreaWidget: ads.CDockAreaWidget, /, TabIndex: int = -1) -> None:
            ...
        def dumpLayout(self) -> None:
            ...
        def event(self, e: PySide6.QtCore.QEvent) -> bool:
            ...
        def features(self) -> ads.CDockWidget.DockWidgetFeature:
            ...
        def floatingWidget(self) -> ads.CFloatingDockContainer:
            ...
        def handleAutoHideWidgetEvent(self, e: PySide6.QtCore.QEvent, w: PySide6.QtWidgets.QWidget) -> None:
            ...
        def hasOpenDockAreas(self) -> bool:
            ...
        def hasTopLevelDockWidget(self) -> bool:
            ...
        def isFloating(self) -> bool:
            ...
        def isInFrontOf(self, Other: ads.CDockContainerWidget) -> bool:
            ...
        def lastAddedDockAreaWidget(self, area: ads.DockWidgetArea) -> ads.CDockAreaWidget:
            ...
        def openedDockAreas(self) -> list[ads.CDockAreaWidget]:
            ...
        def openedDockWidgets(self) -> list[ads.CDockWidget]:
            ...
        def registerAutoHideWidget(self, AutoHideWidget: ads.CAutoHideDockContainer) -> None:
            ...
        def removeAutoHideWidget(self, AutoHideWidget: ads.CAutoHideDockContainer) -> None:
            ...
        def removeDockArea(self, area: ads.CDockAreaWidget) -> None:
            ...
        def removeDockWidget(self, Dockwidget: ads.CDockWidget) -> None:
            ...
        def rootSplitter(self) -> ads.CDockSplitter:
            ...
        def saveState(self, Stream: PySide6.QtCore.QXmlStreamWriter) -> None:
            ...
        def topLevelDockArea(self) -> ads.CDockAreaWidget:
            ...
        def topLevelDockWidget(self) -> ads.CDockWidget:
            ...
        def updateSplitterHandles(self, splitter: PySide6.QtWidgets.QSplitter) -> None:
            ...
        def visibleDockAreaCount(self) -> int:
            ...
        def zOrderIndex(self) -> int:
            ...
    class CDockFocusController(PySide6.QtCore.QObject):
        """
        CDockFocusController(self, DockManager: PySide6QtAds.ads.CDockManager, /) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockFocusController" inherits "QObject":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, DockManager: PySide6QtAds.ads.CDockManager, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def clearDockWidgetFocus(self, dockWidget: ads.CDockWidget) -> None:
            ...
        def focusedDockArea(self) -> ads.CDockAreaWidget:
            ...
        def focusedDockWidget(self) -> ads.CDockWidget:
            ...
        def notifyFloatingWidgetDrop(self, FloatingWidget: ads.CFloatingDockContainer) -> None:
            ...
        def notifyWidgetOrAreaRelocation(self, RelocatedWidget: PySide6.QtWidgets.QWidget) -> None:
            ...
        def setDockWidgetFocused(self, focusedNow: ads.CDockWidget) -> None:
            ...
        def setDockWidgetTabFocused(self, Tab: ads.CDockWidgetTab) -> None:
            ...
        def setDockWidgetTabPressed(self, Value: bool) -> None:
            ...
    class CDockManager(ads.CDockContainerWidget):
        """
        CDockManager(self, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        """
        class ColorSchemeMode(enum.IntEnum):
            """
            An enumeration.
            """
            Dark: typing.ClassVar[ads.CDockManager.ColorSchemeMode]  # value = <ColorSchemeMode.Dark: 1>
            FollowPalette: typing.ClassVar[ads.CDockManager.ColorSchemeMode]  # value = <ColorSchemeMode.FollowPalette: 2>
            Light: typing.ClassVar[ads.CDockManager.ColorSchemeMode]  # value = <ColorSchemeMode.Light: 0>
        class eAutoHideFlag(enum.IntFlag):
            """
            An enumeration.
            """
            AutoHideButtonCheckable: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideButtonCheckable: 8>
            AutoHideButtonTogglesArea: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideButtonTogglesArea: 4>
            AutoHideCloseButtonCollapsesDock: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideCloseButtonCollapsesDock: 64>
            AutoHideCloseOnOutsideMouseClick: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideCloseOnOutsideMouseClick: 1024>
            AutoHideFeatureEnabled: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideFeatureEnabled: 1>
            AutoHideHasCloseButton: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideHasCloseButton: 128>
            AutoHideHasMinimizeButton: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideHasMinimizeButton: 256>
            AutoHideOpenOnDragHover: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideOpenOnDragHover: 512>
            AutoHideShowOnMouseOver: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideShowOnMouseOver: 32>
            AutoHideSideBarsIconOnly: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.AutoHideSideBarsIconOnly: 16>
            DefaultAutoHideConfig: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.DefaultAutoHideConfig: 1283>
            DockAreaHasAutoHideButton: typing.ClassVar[ads.CDockManager.eAutoHideFlag]  # value = <eAutoHideFlag.DockAreaHasAutoHideButton: 2>
        class eConfigFlag(enum.IntFlag):
            """
            An enumeration.
            """
            ActiveTabHasCloseButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.ActiveTabHasCloseButton: 1>
            AllTabsHaveCloseButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.AllTabsHaveCloseButton: 128>
            AlwaysShowTabs: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.AlwaysShowTabs: 8192>
            DefaultBaseConfig: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DefaultBaseConfig: 268746787>
            DefaultDockAreaButtons: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DefaultDockAreaButtons: 49154>
            DefaultNonOpaqueConfig: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DefaultNonOpaqueConfig: 268748835>
            DefaultOpaqueConfig: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DefaultOpaqueConfig: 268748843>
            DisableStylesheet: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DisableStylesheet: 2147483648>
            DisableTabTextEliding: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DisableTabTextEliding: 67108864>
            DockAreaCloseButtonClosesTab: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaCloseButtonClosesTab: 4>
            DockAreaDynamicTabsMenuButtonVisibility: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaDynamicTabsMenuButtonVisibility: 131072>
            DockAreaHasCloseButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaHasCloseButton: 2>
            DockAreaHasTabsMenuButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaHasTabsMenuButton: 32768>
            DockAreaHasUndockButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaHasUndockButton: 16384>
            DockAreaHideDisabledButtons: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DockAreaHideDisabledButtons: 65536>
            DoubleClickUndocksWidget: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DoubleClickUndocksWidget: 268435456>
            DragPreviewHasWindowFrame: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DragPreviewHasWindowFrame: 4096>
            DragPreviewIsDynamic: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DragPreviewIsDynamic: 1024>
            DragPreviewShowsContentPixmap: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.DragPreviewShowsContentPixmap: 2048>
            EqualSplitOnInsertion: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.EqualSplitOnInsertion: 4194304>
            FloatingContainerForceNativeTitleBar: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FloatingContainerForceNativeTitleBar: 8388608>
            FloatingContainerForceQWidgetTitleBar: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FloatingContainerForceQWidgetTitleBar: 16777216>
            FloatingContainerHasWidgetIcon: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FloatingContainerHasWidgetIcon: 524288>
            FloatingContainerHasWidgetTitle: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FloatingContainerHasWidgetTitle: 262144>
            FocusHighlighting: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.FocusHighlighting: 2097152>
            HideSingleCentralWidgetTitleBar: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.HideSingleCentralWidgetTitleBar: 1048576>
            MiddleMouseButtonClosesTab: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.MiddleMouseButtonClosesTab: 33554432>
            NonOpaqueWithWindowFrame: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.NonOpaqueWithWindowFrame: 268752931>
            OpaqueSplitterResize: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.OpaqueSplitterResize: 8>
            RetainTabSizeWhenCloseButtonHidden: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.RetainTabSizeWhenCloseButtonHidden: 256>
            ShowTabTextOnlyForActiveTab: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.ShowTabTextOnlyForActiveTab: 134217728>
            TabCloseButtonIsToolButton: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.TabCloseButtonIsToolButton: 64>
            TabsAtBottom: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.TabsAtBottom: 536870912>
            UseNativeWindows: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.UseNativeWindows: 1073741824>
            XmlAutoFormattingEnabled: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.XmlAutoFormattingEnabled: 16>
            XmlCompressionEnabled: typing.ClassVar[ads.CDockManager.eConfigFlag]  # value = <eConfigFlag.XmlCompressionEnabled: 32>
        class eConfigParam(enum.IntFlag):
            """
            An enumeration.
            """
            AutoHideOpenOnDragHoverDelay_ms: typing.ClassVar[ads.CDockManager.eConfigParam]  # value = <eConfigParam.AutoHideOpenOnDragHoverDelay_ms: 0>
            ConfigParamCount: typing.ClassVar[ads.CDockManager.eConfigParam]  # value = <eConfigParam.ConfigParamCount: 1>
        class eViewMenuInsertionOrder(enum.IntEnum):
            """
            An enumeration.
            """
            MenuAlphabeticallySorted: typing.ClassVar[ads.CDockManager.eViewMenuInsertionOrder]  # value = <eViewMenuInsertionOrder.MenuAlphabeticallySorted: 1>
            MenuSortedByInsertion: typing.ClassVar[ads.CDockManager.eViewMenuInsertionOrder]  # value = <eViewMenuInsertionOrder.MenuSortedByInsertion: 0>
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockManager" inherits "ads::CDockContainerWidget":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def autoHideConfigFlags() -> ads.CDockManager.eAutoHideFlag:
            ...
        @staticmethod
        def configFlags() -> ads.CDockManager.eConfigFlag:
            ...
        @staticmethod
        def configParam(Param: ads.CDockManager.eConfigParam, Default: typing.Any) -> typing.Any:
            ...
        @staticmethod
        def dockAreaCreated(*args, **kwargs):
            ...
        @staticmethod
        def dockWidgetAboutToBeRemoved(*args, **kwargs):
            ...
        @staticmethod
        def dockWidgetAdded(*args, **kwargs):
            ...
        @staticmethod
        def dockWidgetRemoved(*args, **kwargs):
            ...
        @staticmethod
        def floatingContainersTitle() -> str:
            ...
        @staticmethod
        def floatingWidgetCreated(*args, **kwargs):
            ...
        @staticmethod
        def focusedDockWidgetChanged(*args, **kwargs):
            ...
        @staticmethod
        def iconProvider() -> ads.CIconProvider:
            ...
        @staticmethod
        def isApplicationPaletteDark() -> bool:
            ...
        @staticmethod
        def openingPerspective(*args, **kwargs):
            ...
        @staticmethod
        def perspectiveListChanged(*args, **kwargs):
            ...
        @staticmethod
        def perspectiveListLoaded(*args, **kwargs):
            ...
        @staticmethod
        def perspectiveOpened(*args, **kwargs):
            ...
        @staticmethod
        def perspectivesRemoved(*args, **kwargs):
            ...
        @staticmethod
        def restoringState(*args, **kwargs):
            ...
        @staticmethod
        def setAutoHideConfigFlag(Flag: ads.CDockManager.eAutoHideFlag, /, On: bool = True) -> None:
            ...
        @staticmethod
        def setAutoHideConfigFlags(Flags: ads.CDockManager.eAutoHideFlag) -> None:
            ...
        @staticmethod
        def setConfigFlag(Flag: ads.CDockManager.eConfigFlag, /, On: bool = True) -> None:
            ...
        @staticmethod
        def setConfigFlags(Flags: ads.CDockManager.eConfigFlag) -> None:
            ...
        @staticmethod
        def setConfigParam(Param: ads.CDockManager.eConfigParam, Value: typing.Any) -> None:
            ...
        @staticmethod
        def setFloatingContainersTitle(Title: str) -> None:
            ...
        @staticmethod
        def startDragDistance() -> int:
            ...
        @staticmethod
        def stateRestored(*args, **kwargs):
            ...
        @staticmethod
        def testAutoHideConfigFlag(Flag: ads.CDockManager.eAutoHideFlag) -> bool:
            ...
        @staticmethod
        def testConfigFlag(Flag: ads.CDockManager.eConfigFlag) -> bool:
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def addAutoHideDockWidget(self, Location: ads.SideBarLocation, Dockwidget: ads.CDockWidget) -> ads.CAutoHideDockContainer:
            ...
        def addAutoHideDockWidgetToContainer(self, Location: ads.SideBarLocation, Dockwidget: ads.CDockWidget, DockContainerWidget: ads.CDockContainerWidget) -> ads.CAutoHideDockContainer:
            ...
        def addDockWidget(self, area: ads.DockWidgetArea, Dockwidget: ads.CDockWidget, /, DockAreaWidget: PySide6QtAds.ads.CDockAreaWidget | None = None, Index: int = -1) -> ads.CDockAreaWidget:
            ...
        def addDockWidgetFloating(self, Dockwidget: ads.CDockWidget) -> ads.CFloatingDockContainer:
            ...
        def addDockWidgetTab(self, area: ads.DockWidgetArea, Dockwidget: ads.CDockWidget) -> ads.CDockAreaWidget:
            ...
        def addDockWidgetTabToArea(self, Dockwidget: ads.CDockWidget, DockAreaWidget: ads.CDockAreaWidget, /, Index: int = -1) -> ads.CDockAreaWidget:
            ...
        def addDockWidgetToContainer(self, area: ads.DockWidgetArea, Dockwidget: ads.CDockWidget, DockContainerWidget: ads.CDockContainerWidget) -> ads.CDockAreaWidget:
            ...
        def addPerspective(self, UniquePrespectiveName: str) -> None:
            ...
        def addToggleViewActionToMenu(self, ToggleViewAction: PySide6.QtGui.QAction, /, Group: str = '', GroupIcon: PySide6.QtGui.QIcon | PySide6.QtGui.QPixmap = ...) -> PySide6.QtGui.QAction:
            ...
        def centralWidget(self) -> ads.CDockWidget:
            ...
        def changeEvent(self, event: PySide6.QtCore.QEvent) -> None:
            ...
        def containerOverlay(self) -> ads.CDockOverlay:
            ...
        def createDockWidget(self, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> ads.CDockWidget:
            ...
        def dockAreaOverlay(self) -> ads.CDockOverlay:
            ...
        def dockContainers(self) -> list[ads.CDockContainerWidget]:
            ...
        def dockFocusController(self) -> ads.CDockFocusController:
            ...
        def dockWidgetToolBarIconSize(self, State: ads.CDockWidget.eState) -> PySide6.QtCore.QSize:
            ...
        def dockWidgetToolBarStyle(self, State: ads.CDockWidget.eState) -> PySide6.QtCore.Qt.ToolButtonStyle:
            ...
        def dockWidgetsMap(self) -> dict[str, ads.CDockWidget]:
            ...
        def endLeavingMinimizedState(self) -> None:
            ...
        def eventFilter(self, obj: PySide6.QtCore.QObject, e: PySide6.QtCore.QEvent) -> bool:
            ...
        def findDockWidget(self, ObjectName: str) -> ads.CDockWidget:
            ...
        def floatingWidgets(self) -> list[ads.CFloatingDockContainer]:
            ...
        def focusedDockWidget(self) -> ads.CDockWidget:
            ...
        def globallyLockedDockWidgetFeatures(self) -> ads.CDockWidget.DockWidgetFeature:
            ...
        def hideManagerAndFloatingWidgets(self) -> None:
            ...
        def isDesiredStylesheetDark(self) -> bool:
            ...
        def isLeavingMinimizedState(self) -> bool:
            ...
        def isRestoringState(self) -> bool:
            ...
        def loadPerspectives(self, Settings: PySide6.QtCore.QSettings) -> None:
            ...
        def lockDockWidgetFeaturesGlobally(self, /, Features: ads.CDockWidget.DockWidgetFeature = ...) -> None:
            ...
        def notifyFloatingWidgetDrop(self, FloatingWidget: ads.CFloatingDockContainer) -> None:
            ...
        def notifyWidgetOrAreaRelocation(self, RelocatedWidget: PySide6.QtWidgets.QWidget) -> None:
            ...
        def openPerspective(self, PerspectiveName: str) -> None:
            ...
        def perspectiveNames(self) -> list[str]:
            ...
        def raise_(self) -> None:
            ...
        def registerDockContainer(self, DockContainer: ads.CDockContainerWidget) -> None:
            ...
        def registerFloatingWidget(self, FloatingWidget: ads.CFloatingDockContainer) -> None:
            ...
        def removeDockContainer(self, DockContainer: ads.CDockContainerWidget) -> None:
            ...
        def removeDockWidget(self, Dockwidget: ads.CDockWidget) -> None:
            ...
        def removeFloatingWidget(self, FloatingWidget: ads.CFloatingDockContainer) -> None:
            ...
        def removePerspective(self, Name: str) -> None:
            ...
        def removePerspectives(self, Names: collections.abc.Sequence[str]) -> None:
            ...
        def restoreHiddenFloatingWidgets(self) -> None:
            ...
        def restoreState(self, state: PySide6.QtCore.QByteArray | bytes | bytearray | memoryview, /, version: int | None = None) -> bool:
            ...
        def savePerspectives(self, Settings: PySide6.QtCore.QSettings) -> None:
            ...
        def saveState(self, /, version: int | None = None) -> PySide6.QtCore.QByteArray:
            ...
        def setCentralWidget(self, widget: ads.CDockWidget) -> ads.CDockAreaWidget:
            ...
        def setColorSchemeMode(self, Mode: ads.CDockManager.ColorSchemeMode) -> None:
            ...
        def setComponentsFactory(self, Factory: ads.CDockComponentsFactory) -> None:
            ...
        def setDockWidgetFocused(self, DockWidget: ads.CDockWidget) -> None:
            ...
        def setDockWidgetToolBarIconSize(self, IconSize: PySide6.QtCore.QSize, State: ads.CDockWidget.eState) -> None:
            ...
        def setDockWidgetToolBarStyle(self, Style: PySide6.QtCore.Qt.ToolButtonStyle, State: ads.CDockWidget.eState) -> None:
            ...
        def setSplitterSizes(self, ContainedArea: ads.CDockAreaWidget, sizes: collections.abc.Sequence[int]) -> None:
            ...
        def setViewMenuInsertionOrder(self, Order: ads.CDockManager.eViewMenuInsertionOrder) -> None:
            ...
        def showEvent(self, event: PySide6.QtGui.QShowEvent) -> None:
            ...
        def splitterSizes(self, ContainedArea: ads.CDockAreaWidget) -> list[int]:
            ...
        def viewMenu(self) -> PySide6.QtWidgets.QMenu:
            ...
        def zOrderIndex(self) -> int:
            ...
    class CDockOverlay(PySide6.QtWidgets.QFrame):
        """
        CDockOverlay(self, parent: PySide6.QtWidgets.QWidget, /, Mode: PySide6QtAds.ads.CDockOverlay.eMode = Instance(PySide6QtAds.ads.CDockOverlay.eMode.ModeDockAreaOverlay)) -> None
        """
        class eMode(enum.IntEnum):
            """
            An enumeration.
            """
            ModeContainerOverlay: typing.ClassVar[ads.CDockOverlay.eMode]  # value = <eMode.ModeContainerOverlay: 1>
            ModeDockAreaOverlay: typing.ClassVar[ads.CDockOverlay.eMode]  # value = <eMode.ModeDockAreaOverlay: 0>
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockOverlay" inherits "QFrame":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, parent: PySide6.QtWidgets.QWidget, /, Mode: PySide6QtAds.ads.CDockOverlay.eMode = Instance(PySide6QtAds.ads.CDockOverlay.eMode.ModeDockAreaOverlay)) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def allowedAreas(self) -> ads.DockWidgetArea:
            ...
        def dropAreaUnderCursor(self) -> ads.DockWidgetArea:
            """
            dropAreaUnderCursor(self, GlobalPos: PySide6.QtCore.QPoint, /) -> PySide6QtAds.ads.DockWidgetArea
            """
        def dropOverlayRect(self) -> PySide6.QtCore.QRect:
            ...
        def dropPreviewEnabled(self) -> bool:
            ...
        def enableDropPreview(self, Enable: bool) -> None:
            ...
        def event(self, e: PySide6.QtCore.QEvent) -> bool:
            ...
        def hideEvent(self, e: PySide6.QtGui.QHideEvent) -> None:
            ...
        def hideOverlay(self) -> None:
            ...
        def paintEvent(self, e: PySide6.QtGui.QPaintEvent) -> None:
            ...
        def setAllowedArea(self, area: ads.DockWidgetArea, Enable: bool) -> None:
            ...
        def setAllowedAreas(self, areas: ads.DockWidgetArea) -> None:
            ...
        def showEvent(self, e: PySide6.QtGui.QShowEvent) -> None:
            ...
        def showOverlay(self, target: PySide6.QtWidgets.QWidget) -> ads.DockWidgetArea:
            """
            showOverlay(self, target: PySide6.QtWidgets.QWidget, GlobalPos: PySide6.QtCore.QPoint, /) -> PySide6QtAds.ads.DockWidgetArea
            """
        def tabIndexUnderCursor(self) -> int:
            ...
        def visibleDropAreaUnderCursor(self) -> ads.DockWidgetArea:
            """
            visibleDropAreaUnderCursor(self, GlobalPos: PySide6.QtCore.QPoint, /) -> PySide6QtAds.ads.DockWidgetArea
            """
    class CDockOverlayCross(PySide6.QtWidgets.QWidget):
        """
        CDockOverlayCross(self, overlay: PySide6QtAds.ads.CDockOverlay, /, *, iconColors: str | None = None, iconFrameColor: PySide6.QtGui.QColor | None = None, iconBackgroundColor: PySide6.QtGui.QColor | None = None, iconOverlayColor: PySide6.QtGui.QColor | None = None, iconArrowColor: PySide6.QtGui.QColor | None = None, iconShadowColor: PySide6.QtGui.QColor | None = None) -> None
        """
        class eIconColor(enum.IntEnum):
            """
            An enumeration.
            """
            ArrowColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.ArrowColor: 3>
            FrameColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.FrameColor: 0>
            OverlayColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.OverlayColor: 2>
            ShadowColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.ShadowColor: 4>
            WindowBackgroundColor: typing.ClassVar[ads.CDockOverlayCross.eIconColor]  # value = <eIconColor.WindowBackgroundColor: 1>
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockOverlayCross" inherits "QWidget":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, overlay: PySide6QtAds.ads.CDockOverlay, /, *, iconColors: str | None = None, iconFrameColor: PySide6.QtGui.QColor | None = None, iconBackgroundColor: PySide6.QtGui.QColor | None = None, iconOverlayColor: PySide6.QtGui.QColor | None = None, iconArrowColor: PySide6.QtGui.QColor | None = None, iconShadowColor: PySide6.QtGui.QColor | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def cursorLocation(self) -> ads.DockWidgetArea:
            """
            cursorLocation(self, GlobalPos: PySide6.QtCore.QPoint, /) -> PySide6QtAds.ads.DockWidgetArea
            """
        def event(self, e: PySide6.QtCore.QEvent) -> bool:
            ...
        def iconColor(self) -> PySide6.QtGui.QColor:
            """
            iconColor(self, ColorIndex: PySide6QtAds.ads.CDockOverlayCross.eIconColor, /) -> PySide6.QtGui.QColor
            """
        def iconColors(self) -> str:
            ...
        def reset(self) -> None:
            ...
        def setAreaWidgets(self, widgets: dict[ads.DockWidgetArea, PySide6.QtWidgets.QWidget]) -> None:
            ...
        def setIconArrowColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
            ...
        def setIconBackgroundColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
            ...
        def setIconColor(self, ColorIndex: ads.CDockOverlayCross.eIconColor, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
            ...
        def setIconColors(self, Colors: str) -> None:
            ...
        def setIconFrameColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
            ...
        def setIconOverlayColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
            ...
        def setIconShadowColor(self, Color: PySide6.QtGui.QColor | str | PySide6.QtGui.QRgba64 | typing.Any | PySide6.QtCore.Qt.GlobalColor | int) -> None:
            ...
        def setupOverlayCross(self, Mode: ads.CDockOverlay.eMode) -> None:
            ...
        def showEvent(self, e: PySide6.QtGui.QShowEvent) -> None:
            ...
        def updateOverlayIcons(self) -> None:
            ...
        def updatePosition(self) -> None:
            ...
    class CDockSplitter(PySide6.QtWidgets.QSplitter):
        """
        CDockSplitter(self, orientation: PySide6.QtCore.Qt.Orientation, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        CDockSplitter(self, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockSplitter" inherits "QSplitter":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, orientation: PySide6.QtCore.Qt.Orientation, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
            __init__(self, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def firstWidget(self) -> PySide6.QtWidgets.QWidget:
            ...
        def hasVisibleContent(self) -> bool:
            ...
        def isResizingWithContainer(self) -> bool:
            ...
        def lastWidget(self) -> PySide6.QtWidgets.QWidget:
            ...
    class CDockWidget(PySide6.QtWidgets.QFrame):
        """
        CDockWidget(self, manager: PySide6QtAds.ads.CDockManager, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        CDockWidget(self, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        """
        class DockWidgetFeature(enum.IntFlag):
            """
            An enumeration.
            """
            AllDockWidgetFeatures: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.AllDockWidgetFeatures: 575>
            CustomCloseHandling: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.CustomCloseHandling: 16>
            DefaultDockWidgetFeatures: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DefaultDockWidgetFeatures: 551>
            DeleteContentOnClose: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DeleteContentOnClose: 256>
            DockWidgetAlwaysCloseAndDelete: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetAlwaysCloseAndDelete: 72>
            DockWidgetClosable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetClosable: 1>
            DockWidgetDeleteOnClose: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetDeleteOnClose: 8>
            DockWidgetFloatable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetFloatable: 4>
            DockWidgetFocusable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetFocusable: 32>
            DockWidgetForceCloseWithArea: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetForceCloseWithArea: 64>
            DockWidgetMovable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetMovable: 2>
            DockWidgetPinnable: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.DockWidgetPinnable: 512>
            GloballyLockableFeatures: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.GloballyLockableFeatures: 519>
            NoDockWidgetFeatures: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.NoDockWidgetFeatures: 0>
            NoTab: typing.ClassVar[ads.CDockWidget.DockWidgetFeature]  # value = <DockWidgetFeature.NoTab: 128>
        class eInsertMode(enum.IntEnum):
            """
            An enumeration.
            """
            AutoScrollArea: typing.ClassVar[ads.CDockWidget.eInsertMode]  # value = <eInsertMode.AutoScrollArea: 0>
            ForceNoScrollArea: typing.ClassVar[ads.CDockWidget.eInsertMode]  # value = <eInsertMode.ForceNoScrollArea: 2>
            ForceScrollArea: typing.ClassVar[ads.CDockWidget.eInsertMode]  # value = <eInsertMode.ForceScrollArea: 1>
        class eMinimumSizeHintMode(enum.IntEnum):
            """
            An enumeration.
            """
            MinimumSizeHintFromContent: typing.ClassVar[ads.CDockWidget.eMinimumSizeHintMode]  # value = <eMinimumSizeHintMode.MinimumSizeHintFromContent: 1>
            MinimumSizeHintFromContentMinimumSize: typing.ClassVar[ads.CDockWidget.eMinimumSizeHintMode]  # value = <eMinimumSizeHintMode.MinimumSizeHintFromContentMinimumSize: 3>
            MinimumSizeHintFromDockWidget: typing.ClassVar[ads.CDockWidget.eMinimumSizeHintMode]  # value = <eMinimumSizeHintMode.MinimumSizeHintFromDockWidget: 0>
            MinimumSizeHintFromDockWidgetMinimumSize: typing.ClassVar[ads.CDockWidget.eMinimumSizeHintMode]  # value = <eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize: 2>
        class eState(enum.IntEnum):
            """
            An enumeration.
            """
            StateDocked: typing.ClassVar[ads.CDockWidget.eState]  # value = <eState.StateDocked: 1>
            StateFloating: typing.ClassVar[ads.CDockWidget.eState]  # value = <eState.StateFloating: 2>
            StateHidden: typing.ClassVar[ads.CDockWidget.eState]  # value = <eState.StateHidden: 0>
        class eToggleViewActionMode(enum.IntEnum):
            """
            An enumeration.
            """
            ActionModeShow: typing.ClassVar[ads.CDockWidget.eToggleViewActionMode]  # value = <eToggleViewActionMode.ActionModeShow: 1>
            ActionModeToggle: typing.ClassVar[ads.CDockWidget.eToggleViewActionMode]  # value = <eToggleViewActionMode.ActionModeToggle: 0>
        class eToolBarStyleSource(enum.IntEnum):
            """
            An enumeration.
            """
            ToolBarStyleFromDockManager: typing.ClassVar[ads.CDockWidget.eToolBarStyleSource]  # value = <eToolBarStyleSource.ToolBarStyleFromDockManager: 0>
            ToolBarStyleFromDockWidget: typing.ClassVar[ads.CDockWidget.eToolBarStyleSource]  # value = <eToolBarStyleSource.ToolBarStyleFromDockWidget: 1>
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockWidget" inherits "QFrame":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def closeRequested(*args, **kwargs):
            ...
        @staticmethod
        def closed(*args, **kwargs):
            ...
        @staticmethod
        def emitTopLevelEventForWidget(TopLevelDockWidget: ads.CDockWidget, Floating: bool) -> None:
            ...
        @staticmethod
        def featuresChanged(*args, **kwargs):
            ...
        @staticmethod
        def titleChanged(*args, **kwargs):
            ...
        @staticmethod
        def topLevelChanged(*args, **kwargs):
            ...
        @staticmethod
        def viewToggled(*args, **kwargs):
            ...
        @staticmethod
        def visibilityChanged(*args, **kwargs):
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, manager: PySide6QtAds.ads.CDockManager, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
            __init__(self, title: str, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def autoHideDockContainer(self) -> ads.CAutoHideDockContainer:
            ...
        def autoHideLocation(self) -> ads.SideBarLocation:
            ...
        def closeDockWidget(self) -> None:
            ...
        def closeDockWidgetInternal(self, /, ForceClose: bool = False) -> bool:
            ...
        def createDefaultToolBar(self) -> PySide6.QtWidgets.QToolBar:
            ...
        def deleteDockWidget(self) -> None:
            ...
        def dockAreaWidget(self) -> ads.CDockAreaWidget:
            ...
        def dockContainer(self) -> ads.CDockContainerWidget:
            ...
        def dockManager(self) -> ads.CDockManager:
            ...
        def emitTopLevelChanged(self, Floating: bool) -> None:
            ...
        def event(self, e: PySide6.QtCore.QEvent) -> bool:
            ...
        def features(self) -> ads.CDockWidget.DockWidgetFeature:
            ...
        def flagAsUnassigned(self) -> None:
            ...
        def floatingDockContainer(self) -> ads.CFloatingDockContainer:
            ...
        def icon(self) -> PySide6.QtGui.QIcon:
            ...
        def isAutoHide(self) -> bool:
            ...
        def isCentralWidget(self) -> bool:
            ...
        def isClosed(self) -> bool:
            ...
        def isCurrentTab(self) -> bool:
            ...
        def isFloating(self) -> bool:
            ...
        def isFullScreen(self) -> bool:
            ...
        def isInFloatingContainer(self) -> bool:
            ...
        def isTabbed(self) -> bool:
            ...
        def minimumSizeHint(self) -> PySide6.QtCore.QSize:
            ...
        def minimumSizeHintMode(self) -> ads.CDockWidget.eMinimumSizeHintMode:
            ...
        def notifyFeaturesChanged(self) -> None:
            ...
        def preferredAutoHideSideBarLocation(self) -> ads.SideBarLocation:
            ...
        def raise_(self) -> None:
            ...
        def requestCloseDockWidget(self) -> None:
            ...
        def saveState(self, Stream: PySide6.QtCore.QXmlStreamWriter) -> None:
            ...
        def setAsCurrentTab(self) -> None:
            ...
        def setAutoHide(self, Enable: bool, /, Location: ads.SideBarLocation = ..., TabIndex: int = -1) -> None:
            ...
        def setClosedState(self, Closed: bool) -> None:
            ...
        def setDockArea(self, DockArea: ads.CDockAreaWidget) -> None:
            ...
        def setDockManager(self, DockManager: ads.CDockManager) -> None:
            ...
        def setFeature(self, flag: ads.CDockWidget.DockWidgetFeature, on: bool) -> None:
            ...
        def setFeatures(self, features: ads.CDockWidget.DockWidgetFeature) -> None:
            ...
        def setFloating(self) -> None:
            ...
        def setIcon(self, Icon: PySide6.QtGui.QIcon | PySide6.QtGui.QPixmap) -> None:
            ...
        def setMinimumSizeHintMode(self, Mode: ads.CDockWidget.eMinimumSizeHintMode) -> None:
            ...
        def setPreferredAutoHideSideBarLocation(self, Location: ads.SideBarLocation) -> None:
            ...
        def setSideTabWidget(self, SideTab: ads.CAutoHideTab) -> None:
            ...
        def setTabToolTip(self, text: str) -> None:
            ...
        def setTitleBarActions(self, actions: collections.abc.Sequence[PySide6.QtGui.QAction]) -> None:
            ...
        def setToggleViewAction(self, action: PySide6.QtGui.QAction) -> None:
            ...
        def setToggleViewActionChecked(self, Checked: bool) -> None:
            ...
        def setToggleViewActionMode(self, Mode: ads.CDockWidget.eToggleViewActionMode) -> None:
            ...
        def setToolBar(self, ToolBar: PySide6.QtWidgets.QToolBar) -> None:
            ...
        def setToolBarIconSize(self, IconSize: PySide6.QtCore.QSize, State: ads.CDockWidget.eState) -> None:
            ...
        def setToolBarStyle(self, Style: PySide6.QtCore.Qt.ToolButtonStyle, State: ads.CDockWidget.eState) -> None:
            ...
        def setToolBarStyleSource(self, Source: ads.CDockWidget.eToolBarStyleSource) -> None:
            ...
        def setWidget(self, widget: PySide6.QtWidgets.QWidget, /, InsertMode: ads.CDockWidget.eInsertMode = ...) -> None:
            ...
        def showFullScreen(self) -> None:
            ...
        def showNormal(self) -> None:
            ...
        def sideTabWidget(self) -> ads.CAutoHideTab:
            ...
        def tabWidget(self) -> ads.CDockWidgetTab:
            ...
        def takeWidget(self) -> PySide6.QtWidgets.QWidget:
            ...
        def titleBarActions(self) -> list[PySide6.QtGui.QAction]:
            ...
        def toggleAutoHide(self, /, Location: ads.SideBarLocation = ...) -> None:
            ...
        def toggleView(self, /, Open: bool = True) -> None:
            ...
        def toggleViewAction(self) -> PySide6.QtGui.QAction:
            ...
        def toggleViewInternal(self, Open: bool) -> None:
            ...
        def toolBar(self) -> PySide6.QtWidgets.QToolBar:
            ...
        def toolBarIconSize(self, State: ads.CDockWidget.eState) -> PySide6.QtCore.QSize:
            ...
        def toolBarStyle(self, State: ads.CDockWidget.eState) -> PySide6.QtCore.Qt.ToolButtonStyle:
            ...
        def toolBarStyleSource(self) -> ads.CDockWidget.eToolBarStyleSource:
            ...
        def widget(self) -> PySide6.QtWidgets.QWidget:
            ...
    class CDockWidgetTab(PySide6.QtWidgets.QFrame):
        """
        CDockWidgetTab(self, DockWidget: PySide6QtAds.ads.CDockWidget, /, parent: PySide6.QtWidgets.QWidget | None = None, *, activeTab: bool | None = None, iconSize: PySide6.QtCore.QSize | None = None) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CDockWidgetTab" inherits "QFrame":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def activeTabChanged(*args, **kwargs):
            ...
        @staticmethod
        def clicked(*args, **kwargs):
            ...
        @staticmethod
        def closeOtherTabsRequested(*args, **kwargs):
            ...
        @staticmethod
        def closeRequested(*args, **kwargs):
            ...
        @staticmethod
        def elidedChanged(*args, **kwargs):
            ...
        @staticmethod
        def moved(*args, **kwargs):
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, DockWidget: PySide6QtAds.ads.CDockWidget, /, parent: PySide6.QtWidgets.QWidget | None = None, *, activeTab: bool | None = None, iconSize: PySide6.QtCore.QSize | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def buildContextMenu(self, arg__1: PySide6.QtWidgets.QMenu) -> PySide6.QtWidgets.QMenu:
            ...
        def contextMenuEvent(self, ev: PySide6.QtGui.QContextMenuEvent) -> None:
            ...
        def dockAreaWidget(self) -> ads.CDockAreaWidget:
            ...
        def dockWidget(self) -> ads.CDockWidget:
            ...
        def dragState(self) -> ads.eDragState:
            ...
        def event(self, e: PySide6.QtCore.QEvent) -> bool:
            ...
        def icon(self) -> PySide6.QtGui.QIcon:
            ...
        def iconSize(self) -> PySide6.QtCore.QSize:
            ...
        def isActiveTab(self) -> bool:
            ...
        def isClosable(self) -> bool:
            ...
        def isTitleElided(self) -> bool:
            ...
        def mouseDoubleClickEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mouseMoveEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mousePressEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mouseReleaseEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def setActiveTab(self, active: bool) -> None:
            ...
        def setDockAreaWidget(self, DockArea: ads.CDockAreaWidget) -> None:
            ...
        def setElideMode(self, mode: PySide6.QtCore.Qt.TextElideMode) -> None:
            ...
        def setIcon(self, Icon: PySide6.QtGui.QIcon | PySide6.QtGui.QPixmap) -> None:
            ...
        def setIconSize(self, Size: PySide6.QtCore.QSize) -> None:
            ...
        def setText(self, title: str) -> None:
            ...
        def setVisible(self, visible: bool) -> None:
            ...
        def text(self) -> str:
            ...
        def updateStyle(self) -> None:
            ...
    class CDockingStateReader(PySide6.QtCore.QXmlStreamReader):
        """
        CDockingStateReader(self, /) -> None
        """
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def fileVersion(self) -> int:
            ...
        def setFileVersion(self, FileVersion: int) -> None:
            ...
    class CElidingLabel(PySide6.QtWidgets.QLabel):
        """
        CElidingLabel(self, text: str, /, parent: PySide6.QtWidgets.QWidget | None = None, f: PySide6.QtCore.Qt.WindowType = Default(Qt.WindowFlags )) -> None
        CElidingLabel(self, /, parent: PySide6.QtWidgets.QWidget | None = None, f: PySide6.QtCore.Qt.WindowType = Default(Qt.WindowFlags )) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CElidingLabel" inherits "QLabel":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def clicked(*args, **kwargs):
            ...
        @staticmethod
        def doubleClicked(*args, **kwargs):
            ...
        @staticmethod
        def elidedChanged(*args, **kwargs):
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, text: str, /, parent: PySide6.QtWidgets.QWidget | None = None, f: PySide6.QtCore.Qt.WindowType = Default(Qt.WindowFlags )) -> None
            __init__(self, /, parent: PySide6.QtWidgets.QWidget | None = None, f: PySide6.QtCore.Qt.WindowType = Default(Qt.WindowFlags )) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def elideMode(self) -> PySide6.QtCore.Qt.TextElideMode:
            ...
        def isElided(self) -> bool:
            ...
        def minimumSizeHint(self) -> PySide6.QtCore.QSize:
            ...
        def mouseDoubleClickEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mouseReleaseEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
            ...
        def setElideMode(self, mode: PySide6.QtCore.Qt.TextElideMode) -> None:
            ...
        def setText(self, text: str) -> None:
            ...
        def sizeHint(self) -> PySide6.QtCore.QSize:
            ...
        def text(self) -> str:
            ...
    class CFloatingDockContainer(PySide6.QtWidgets.QDockWidget, ads.IFloatingWidget):
        """
        CFloatingDockContainer(self, DockManager: PySide6QtAds.ads.CDockManager, /) -> None
        CFloatingDockContainer(self, DockArea: PySide6QtAds.ads.CDockAreaWidget, /) -> None
        CFloatingDockContainer(self, DockWidget: PySide6QtAds.ads.CDockWidget, /) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CFloatingDockContainer" inherits "QDockWidget":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def startPlatformDrag(FloatingWidget: ads.CFloatingDockContainer, GlobalPressPos: PySide6.QtCore.QPoint, DragSource: PySide6.QtWidgets.QWidget, /, DragOffset: PySide6.QtCore.QPoint | None = None) -> PySide6.QtCore.Qt.DropAction:
            ...
        @staticmethod
        def waylandMoveOrLeaveInWindowPreview(Preview: ads.CFloatingDragPreview, SourceWindow: PySide6.QtWidgets.QWidget, GlobalPos: PySide6.QtCore.QPoint) -> bool:
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, DockManager: PySide6QtAds.ads.CDockManager, /) -> None
            __init__(self, DockArea: PySide6QtAds.ads.CDockAreaWidget, /) -> None
            __init__(self, DockWidget: PySide6QtAds.ads.CDockWidget, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def changeEvent(self, event: PySide6.QtCore.QEvent) -> None:
            ...
        def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
            ...
        def deleteContent(self) -> None:
            ...
        def dockContainer(self) -> ads.CDockContainerWidget:
            ...
        def dockWidgets(self) -> list[ads.CDockWidget]:
            ...
        def event(self, e: PySide6.QtCore.QEvent) -> bool:
            ...
        def finishDragging(self) -> None:
            ...
        def finishDropOperation(self) -> None:
            ...
        def hasNativeTitleBar(self) -> bool:
            ...
        def hasTopLevelDockWidget(self) -> bool:
            ...
        def hideEvent(self, event: PySide6.QtGui.QHideEvent) -> None:
            ...
        def initFloatingGeometry(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize) -> None:
            ...
        def isClosable(self) -> bool:
            ...
        def isDraggingActive(self) -> bool:
            ...
        def isMaximized(self) -> bool:
            ...
        def moveEvent(self, event: PySide6.QtGui.QMoveEvent) -> None:
            ...
        def moveFloating(self) -> None:
            ...
        def onMaximizeRequest(self) -> None:
            ...
        def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
            ...
        def show(self) -> None:
            ...
        def showEvent(self, event: PySide6.QtGui.QShowEvent) -> None:
            ...
        def showMaximized(self) -> None:
            ...
        def showNormal(self, /, fixGeometry: bool = False) -> None:
            ...
        def startDragging(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize, MouseEventHandler: PySide6.QtWidgets.QWidget) -> None:
            ...
        def startFloating(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize, DragState: ads.eDragState, MouseEventHandler: PySide6.QtWidgets.QWidget) -> None:
            ...
        def topLevelDockWidget(self) -> ads.CDockWidget:
            ...
        def updateWindowTitle(self) -> None:
            ...
        def windowHandle(self) -> PySide6.QtGui.QWindow:
            ...
    class CFloatingDragPreview(PySide6.QtWidgets.QWidget, ads.IFloatingWidget):
        """
        CFloatingDragPreview(self, Content: PySide6QtAds.ads.CDockAreaWidget, /) -> None
        CFloatingDragPreview(self, Content: PySide6QtAds.ads.CDockWidget, /) -> None
        CFloatingDragPreview(self, Content: PySide6.QtWidgets.QWidget, parent: PySide6.QtWidgets.QWidget, /) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CFloatingDragPreview" inherits "QWidget":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        @staticmethod
        def draggingCanceled(*args, **kwargs):
            ...
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, Content: PySide6QtAds.ads.CDockAreaWidget, /) -> None
            __init__(self, Content: PySide6QtAds.ads.CDockWidget, /) -> None
            __init__(self, Content: PySide6.QtWidgets.QWidget, parent: PySide6.QtWidgets.QWidget, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def cancelDraggingSilently(self) -> None:
            ...
        def cleanupAutoHideContainerWidget(self, ContainerDropArea: ads.DockWidgetArea) -> None:
            ...
        def eventFilter(self, watched: PySide6.QtCore.QObject, event: PySide6.QtCore.QEvent) -> bool:
            ...
        def finishDragging(self) -> None:
            ...
        def moveFloating(self) -> None:
            """
            moveFloating(self, GlobalPos: PySide6.QtCore.QPoint, /) -> None
            """
        def paintEvent(self, e: PySide6.QtGui.QPaintEvent) -> None:
            ...
        def setSourceContainer(self, Container: ads.CDockContainerWidget) -> None:
            ...
        def startFloating(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize, DragState: ads.eDragState, MouseEventHandler: PySide6.QtWidgets.QWidget) -> None:
            ...
    class CIconProvider(Shiboken.Object):
        """
        CIconProvider(self, /) -> None
        """
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def customIcon(self, IconId: ads.eIcon) -> PySide6.QtGui.QIcon:
            ...
        def registerCustomIcon(self, IconId: ads.eIcon, icon: PySide6.QtGui.QIcon | PySide6.QtGui.QPixmap) -> None:
            ...
    class CPushButton(PySide6.QtWidgets.QPushButton):
        """
        CPushButton(self, /) -> None
        """
        class Orientation(enum.IntEnum):
            """
            An enumeration.
            """
            Horizontal: typing.ClassVar[ads.CPushButton.Orientation]  # value = <Orientation.Horizontal: 0>
            VerticalBottomToTop: typing.ClassVar[ads.CPushButton.Orientation]  # value = <Orientation.VerticalBottomToTop: 2>
            VerticalTopToBottom: typing.ClassVar[ads.CPushButton.Orientation]  # value = <Orientation.VerticalTopToBottom: 1>
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CPushButton" inherits "QPushButton":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def buttonOrientation(self) -> ads.CPushButton.Orientation:
            ...
        def paintEvent(self, event: PySide6.QtGui.QPaintEvent) -> None:
            ...
        def setButtonOrientation(self, orientation: ads.CPushButton.Orientation) -> None:
            ...
        def sizeHint(self) -> PySide6.QtCore.QSize:
            ...
    class CResizeHandle(PySide6.QtWidgets.QFrame):
        """
        CResizeHandle(self, HandlePosition: PySide6.QtCore.Qt.Edge, parent: PySide6.QtWidgets.QWidget, /, *, opaqueResize: bool | None = None) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CResizeHandle" inherits "QFrame":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, HandlePosition: PySide6.QtCore.Qt.Edge, parent: PySide6.QtWidgets.QWidget, /, *, opaqueResize: bool | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def handlePostion(self) -> PySide6.QtCore.Qt.Edge:
            ...
        def isResizing(self) -> bool:
            ...
        def mouseMoveEvent(self, arg__1: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mousePressEvent(self, arg__1: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def mouseReleaseEvent(self, arg__1: PySide6.QtGui.QMouseEvent) -> None:
            ...
        def opaqueResize(self) -> bool:
            ...
        def orientation(self) -> PySide6.QtCore.Qt.Orientation:
            ...
        def setHandlePosition(self, HandlePosition: PySide6.QtCore.Qt.Edge) -> None:
            ...
        def setMaxResizeSize(self, MaxSize: int) -> None:
            ...
        def setMinResizeSize(self, MinSize: int) -> None:
            ...
        def setOpaqueResize(self, /, opaque: bool = True) -> None:
            ...
        def sizeHint(self) -> PySide6.QtCore.QSize:
            ...
    class CSpacerWidget(PySide6.QtWidgets.QWidget):
        """
        CSpacerWidget(self, /, Parent: PySide6.QtWidgets.QWidget | None = None) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CSpacerWidget" inherits "QWidget":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, /, Parent: PySide6.QtWidgets.QWidget | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def minimumSizeHint(self) -> PySide6.QtCore.QSize:
            ...
        def sizeHint(self) -> PySide6.QtCore.QSize:
            ...
    class CTitleBarButton(PySide6.QtWidgets.QToolButton):
        """
        CTitleBarButton(self, ShowInTitleBar: bool, HideWhenDisabled: bool, ButtonId: PySide6QtAds.ads.TitleBarButton, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
        """
        staticMetaObject: typing.ClassVar[PySide6.QtCore.QMetaObject]  # value = PySide6.QtCore.QMetaObject("ads::CTitleBarButton" inherits "QToolButton":...
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, ShowInTitleBar: bool, HideWhenDisabled: bool, ButtonId: PySide6QtAds.ads.TitleBarButton, /, parent: PySide6.QtWidgets.QWidget | None = None) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def buttonId(self) -> ads.TitleBarButton:
            ...
        def event(self, ev: PySide6.QtCore.QEvent) -> bool:
            ...
        def isInAutoHideArea(self) -> bool:
            ...
        def setShowInTitleBar(self, Show: bool) -> None:
            ...
        def setVisible(self, visible: bool) -> None:
            ...
        def titleBar(self) -> ads.CDockAreaTitleBar:
            ...
    class DockWidgetArea(enum.IntFlag):
        """
        An enumeration.
        """
        AllDockAreas: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.AllDockAreas: 31>
        AutoHideDockAreas: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.AutoHideDockAreas: 480>
        BottomAutoHideArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.BottomAutoHideArea: 256>
        BottomDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.BottomDockWidgetArea: 8>
        CenterDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.CenterDockWidgetArea: 16>
        LeftAutoHideArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.LeftAutoHideArea: 32>
        LeftDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.LeftDockWidgetArea: 1>
        NoDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.NoDockWidgetArea: 0>
        OuterDockAreas: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.OuterDockAreas: 15>
        RightAutoHideArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.RightAutoHideArea: 64>
        RightDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.RightDockWidgetArea: 2>
        TopAutoHideArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.TopAutoHideArea: 128>
        TopDockWidgetArea: typing.ClassVar[ads.DockWidgetArea]  # value = <DockWidgetArea.TopDockWidgetArea: 4>
    class IFloatingWidget(Shiboken.Object):
        """
        IFloatingWidget(self, /) -> None
        """
        @staticmethod
        def __new__(type, *args, **kwargs):
            """
            Create and return a new object.  See help(type) for accurate signature.
            """
        def __delattr__(self, name):
            """
            Implement delattr(self, name).
            """
        def __init__(self, *args, **kwargs):
            """
            __init__(self, /) -> None
            
            Initialize self.  See help(type(self)) for accurate signature.
            """
        def __setattr__(self, name, value):
            """
            Implement setattr(self, name, value).
            """
        def finishDragging(self) -> None:
            ...
        def moveFloating(self) -> None:
            ...
        def startFloating(self, DragStartMousePos: PySide6.QtCore.QPoint, Size: PySide6.QtCore.QSize, DragState: ads.eDragState, MouseEventHandler: PySide6.QtWidgets.QWidget) -> None:
            ...
    class SideBarLocation(enum.IntEnum):
        """
        An enumeration.
        """
        SideBarBottom: typing.ClassVar[ads.SideBarLocation]  # value = <SideBarLocation.SideBarBottom: 3>
        SideBarLeft: typing.ClassVar[ads.SideBarLocation]  # value = <SideBarLocation.SideBarLeft: 1>
        SideBarNone: typing.ClassVar[ads.SideBarLocation]  # value = <SideBarLocation.SideBarNone: 4>
        SideBarRight: typing.ClassVar[ads.SideBarLocation]  # value = <SideBarLocation.SideBarRight: 2>
        SideBarTop: typing.ClassVar[ads.SideBarLocation]  # value = <SideBarLocation.SideBarTop: 0>
    class TitleBarButton(enum.IntEnum):
        """
        An enumeration.
        """
        TitleBarButtonAutoHide: typing.ClassVar[ads.TitleBarButton]  # value = <TitleBarButton.TitleBarButtonAutoHide: 3>
        TitleBarButtonClose: typing.ClassVar[ads.TitleBarButton]  # value = <TitleBarButton.TitleBarButtonClose: 2>
        TitleBarButtonMinimize: typing.ClassVar[ads.TitleBarButton]  # value = <TitleBarButton.TitleBarButtonMinimize: 4>
        TitleBarButtonTabsMenu: typing.ClassVar[ads.TitleBarButton]  # value = <TitleBarButton.TitleBarButtonTabsMenu: 0>
        TitleBarButtonUndock: typing.ClassVar[ads.TitleBarButton]  # value = <TitleBarButton.TitleBarButtonUndock: 1>
    class eBitwiseOperator(enum.IntEnum):
        """
        An enumeration.
        """
        BitwiseAnd: typing.ClassVar[ads.eBitwiseOperator]  # value = <eBitwiseOperator.BitwiseAnd: 0>
        BitwiseOr: typing.ClassVar[ads.eBitwiseOperator]  # value = <eBitwiseOperator.BitwiseOr: 1>
    class eDragState(enum.IntEnum):
        """
        An enumeration.
        """
        DraggingFloatingWidget: typing.ClassVar[ads.eDragState]  # value = <eDragState.DraggingFloatingWidget: 3>
        DraggingInactive: typing.ClassVar[ads.eDragState]  # value = <eDragState.DraggingInactive: 0>
        DraggingMousePressed: typing.ClassVar[ads.eDragState]  # value = <eDragState.DraggingMousePressed: 1>
        DraggingTab: typing.ClassVar[ads.eDragState]  # value = <eDragState.DraggingTab: 2>
    class eIcon(enum.IntEnum):
        """
        An enumeration.
        """
        AutoHideIcon: typing.ClassVar[ads.eIcon]  # value = <eIcon.AutoHideIcon: 1>
        DockAreaCloseIcon: typing.ClassVar[ads.eIcon]  # value = <eIcon.DockAreaCloseIcon: 4>
        DockAreaMenuIcon: typing.ClassVar[ads.eIcon]  # value = <eIcon.DockAreaMenuIcon: 2>
        DockAreaMinimizeIcon: typing.ClassVar[ads.eIcon]  # value = <eIcon.DockAreaMinimizeIcon: 5>
        DockAreaUndockIcon: typing.ClassVar[ads.eIcon]  # value = <eIcon.DockAreaUndockIcon: 3>
        IconCount: typing.ClassVar[ads.eIcon]  # value = <eIcon.IconCount: 6>
        TabCloseIcon: typing.ClassVar[ads.eIcon]  # value = <eIcon.TabCloseIcon: 0>
    class eTabIndex(enum.IntEnum):
        """
        An enumeration.
        """
        TabDefaultInsertIndex: typing.ClassVar[ads.eTabIndex]  # value = <eTabIndex.TabDefaultInsertIndex: -1>
        TabInvalidIndex: typing.ClassVar[ads.eTabIndex]  # value = <eTabIndex.TabInvalidIndex: -2>
    @staticmethod
    def __new__(type, *args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
AllDockAreas: ads.DockWidgetArea  # value = <DockWidgetArea.AllDockAreas: 31>
AutoHideIcon: ads.eIcon  # value = <eIcon.AutoHideIcon: 1>
BitwiseAnd: ads.eBitwiseOperator  # value = <eBitwiseOperator.BitwiseAnd: 0>
BitwiseOr: ads.eBitwiseOperator  # value = <eBitwiseOperator.BitwiseOr: 1>
BottomDockWidgetArea: ads.DockWidgetArea  # value = <DockWidgetArea.BottomDockWidgetArea: 8>
CenterDockWidgetArea: ads.DockWidgetArea  # value = <DockWidgetArea.CenterDockWidgetArea: 16>
DockAreaCloseIcon: ads.eIcon  # value = <eIcon.DockAreaCloseIcon: 4>
DockAreaMenuIcon: ads.eIcon  # value = <eIcon.DockAreaMenuIcon: 2>
DockAreaMinimizeIcon: ads.eIcon  # value = <eIcon.DockAreaMinimizeIcon: 5>
DockAreaUndockIcon: ads.eIcon  # value = <eIcon.DockAreaUndockIcon: 3>
DraggingFloatingWidget: ads.eDragState  # value = <eDragState.DraggingFloatingWidget: 3>
DraggingInactive: ads.eDragState  # value = <eDragState.DraggingInactive: 0>
DraggingMousePressed: ads.eDragState  # value = <eDragState.DraggingMousePressed: 1>
DraggingTab: ads.eDragState  # value = <eDragState.DraggingTab: 2>
IconCount: ads.eIcon  # value = <eIcon.IconCount: 6>
InvalidDockWidgetArea: ads.DockWidgetArea  # value = <DockWidgetArea.NoDockWidgetArea: 0>
LeftDockWidgetArea: ads.DockWidgetArea  # value = <DockWidgetArea.LeftDockWidgetArea: 1>
NoDockWidgetArea: ads.DockWidgetArea  # value = <DockWidgetArea.NoDockWidgetArea: 0>
OuterDockAreas: ads.DockWidgetArea  # value = <DockWidgetArea.OuterDockAreas: 15>
RightDockWidgetArea: ads.DockWidgetArea  # value = <DockWidgetArea.RightDockWidgetArea: 2>
SideBarBottom: ads.SideBarLocation  # value = <SideBarLocation.SideBarBottom: 3>
SideBarLeft: ads.SideBarLocation  # value = <SideBarLocation.SideBarLeft: 1>
SideBarNone: ads.SideBarLocation  # value = <SideBarLocation.SideBarNone: 4>
SideBarRight: ads.SideBarLocation  # value = <SideBarLocation.SideBarRight: 2>
SideBarTop: ads.SideBarLocation  # value = <SideBarLocation.SideBarTop: 0>
TabCloseIcon: ads.eIcon  # value = <eIcon.TabCloseIcon: 0>
TabDefaultInsertIndex: ads.eTabIndex  # value = <eTabIndex.TabDefaultInsertIndex: -1>
TabInvalidIndex: ads.eTabIndex  # value = <eTabIndex.TabInvalidIndex: -2>
TitleBarButtonAutoHide: ads.TitleBarButton  # value = <TitleBarButton.TitleBarButtonAutoHide: 3>
TitleBarButtonClose: ads.TitleBarButton  # value = <TitleBarButton.TitleBarButtonClose: 2>
TitleBarButtonMinimize: ads.TitleBarButton  # value = <TitleBarButton.TitleBarButtonMinimize: 4>
TitleBarButtonTabsMenu: ads.TitleBarButton  # value = <TitleBarButton.TitleBarButtonTabsMenu: 0>
TitleBarButtonUndock: ads.TitleBarButton  # value = <TitleBarButton.TitleBarButtonUndock: 1>
TopDockWidgetArea: ads.DockWidgetArea  # value = <DockWidgetArea.TopDockWidgetArea: 4>
