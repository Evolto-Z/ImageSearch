from threading import Timer
import PyQt6.QtCore as QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap
from core import CorpusCollection
from dirManager import DirManager
from localStorage import StorageKey, localStorage
from misc import adaptSizeToLimitedSize, alphaBlendAntiBG
from snipper import ScreenShotWidget
from PIL import ImageQt, Image
import numpy as np
import cv2 as cv

CANVAS_WIDTH = 512
CANVAS_HEIGHT = 512


class ImageSearchUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.corpusCollection = CorpusCollection()
        self.queryImg = None
        self.resultPath = ''

    def initUI(self):
        btn_selectRootDir = QPushButton('管理目录', self)
        btn_selectRootDir.resize(btn_selectRootDir.sizeHint())
        btn_selectRootDir.clicked.connect(self.onOpenDirManager)

        btn_refreshDir = QPushButton('重新加载', self)
        btn_refreshDir.resize(btn_refreshDir.sizeHint())
        btn_refreshDir.clicked.connect(self.onRefreshAll)

        self.label_query = QLabel()
        self.label_query.setFixedSize(CANVAS_WIDTH, CANVAS_HEIGHT)
        self.label_query.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_query.setStyleSheet("border: 1px dotted black;")
        self.label_result = QLabel()
        self.label_result.setFixedSize(CANVAS_WIDTH, CANVAS_HEIGHT)
        self.label_result.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_result.setStyleSheet("border: 1px dotted black;")

        btn_screenshot = QPushButton('截图')
        btn_screenshot.resize(btn_screenshot.sizeHint())
        btn_screenshot.clicked.connect(self.onOpenSnipper)

        btn_search = QPushButton('搜索')
        btn_search.resize(btn_search.sizeHint())
        btn_search.clicked.connect(self.onSearch)
        
        btn_openResultRoot = QPushButton('查看')
        btn_openResultRoot.resize(btn_openResultRoot.sizeHint())
        btn_openResultRoot.clicked.connect(self.onOpenResultRoot)

        self.label_tips = QLabel()
        self.label_tips.setMaximumHeight(12)

        vbox = QVBoxLayout()
        self.setLayout(vbox)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(btn_selectRootDir)
        hbox1.addWidget(btn_refreshDir)
        hbox1.addStretch(1)
        vbox.addLayout(hbox1)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.label_query)
        hbox2.addSpacing(8)
        hbox2.addWidget(self.label_result)
        vbox.addLayout(hbox2)
        vbox.addStretch(1)
        hbox3 = QHBoxLayout()
        hbox3.addStretch(1)
        hbox3.addWidget(btn_screenshot)
        hbox3.addWidget(btn_search)
        hbox3.addWidget(btn_openResultRoot)
        vbox.addLayout(hbox3)
        vbox.addWidget(self.label_tips)

        self.setFixedSize(2 * CANVAS_WIDTH + 32, CANVAS_HEIGHT + 128)
        self.center()
        self.setWindowTitle('图片搜索器')

        self.snipper = ScreenShotWidget(self.onSnipperEnsure)
        self.dirManager = DirManager(self.onCloseDirManager)

        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def onOpenDirManager(self):
        self.dirManager.show()

    def onCloseDirManager(self, rootDirs):
        localStorage.save(StorageKey.RootDirs, rootDirs)
        self.showTips('正在加载')
        for dir in rootDirs:
            self.corpusCollection.add(dir)
        self.showTips('加载结束')
        
    def onRefreshAll(self):
        self.showTips('正在加载')
        self.corpusCollection.refreshAll()
        self.showTips('加载结束')

    def onOpenSnipper(self):
        self.snipper.start()

    def onSnipperEnsure(self, qImg):
        self.showQImageInLabel(qImg, self.label_query)

    def onSearch(self):
        self.label_result.clear()
        if self.queryImg is not None:
            best, bestMatches = self.corpusCollection.search(self.queryImg)
            if best is None:
                return

            img = cv.imread(best.path, -1)
            img = cv.cvtColor(img, cv.COLOR_BGRA2RGBA)
            if img.ndim == 3 and img.shape[2] == 4:
                img = alphaBlendAntiBG(img)
            self.showImgInLabel(img, self.label_result)
            self.resultPath = best.path

    def showImgInLabel(self, img, label):
        pilImg = Image.fromarray(img)
        qImg = ImageQt.ImageQt(pilImg)
        qPix = QPixmap.fromImage(qImg)

        w, h = adaptSizeToLimitedSize(qPix.width(), qPix.height(), label.width(), label.height(), toLimit=True)
        if w != qPix.width() or h != qPix.height():
            qPix = qPix.scaled(w, h, transformMode=QtCore.Qt.TransformationMode.SmoothTransformation)

        label.setPixmap(qPix)
    
    def showQImageInLabel(self, qImg, label):
        pilImg = ImageQt.fromqimage(qImg)
        self.queryImg = np.array(pilImg)
        qPix = QPixmap.fromImage(qImg)

        w, h = adaptSizeToLimitedSize(qPix.width(), qPix.height(), label.width(), label.height(), toLimit=True)
        if w != qPix.width() or h != qPix.height():
            qPix = qPix.scaled(w, h, transformMode=QtCore.Qt.TransformationMode.SmoothTransformation)

        label.setPixmap(qPix)

    def onOpenResultRoot(self):
        if self.resultPath:
            QFileDialog.getOpenFileName(self, "文件所在目录", self.resultPath, "ImageFile *.jpg *.png")

    def showTips(self, text):
        self.label_tips.setText(text)
