
from PyQt6.QtWidgets import *

from localStorage import StorageKey, localStorage
 
 
class DirManager(QWidget):
    def __init__(self, closeCallback=None):
        super().__init__()
        self.setWindowTitle("根目录管理")
        self.setGeometry(500, 200, 500, 400)

        # create vbox layout object
        vbox = QVBoxLayout()
        # set the layout for the main window
        self.setLayout(vbox)
        # create object of list_widget
        self.list_widget = QListWidget()
        # add items to the listwidget
        self.list_widget.setStyleSheet('background-color:white')

        # add widgets to the vboxlyaout
        vbox.addWidget(self.list_widget)

        btn_add = QPushButton('添加')
        btn_add.resize(btn_add.sizeHint())
        btn_add.clicked.connect(self.addItem)

        btn_remove = QPushButton('删除')
        btn_remove.resize(btn_remove.sizeHint())
        btn_remove.clicked.connect(self.removeItem)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(btn_add)
        hbox.addWidget(btn_remove)
        vbox.addLayout(hbox)

        self.lastPath = localStorage.load(StorageKey.LastPath)
        self.pathMemo = set()
        self.closeCallback = closeCallback

        rootDirs = localStorage.load(StorageKey.RootDirs)
        if rootDirs is not None:
            self.pathMemo = set(rootDirs)
            for path in self.pathMemo:
                self.list_widget.insertItem(self.list_widget.count(), path)
 
    def addItem(self):
        path = QFileDialog.getExistingDirectory(self, "选择根目录", self.lastPath)
        if path:
            self.lastPath = path
            localStorage.save(StorageKey.LastPath, path)
            if path not in self.pathMemo:
                self.pathMemo.add(path)
                self.list_widget.insertItem(self.list_widget.count(), path)

    def removeItem(self):
        listItems=self.list_widget.selectedItems()
        if not listItems: 
            return        
        for item in listItems:
            self.pathMemo.remove(item.text())
            self.list_widget.takeItem(self.list_widget.row(item))

    def getIndependentPaths(self):
        # 因为路径肯定不多，就直接暴力了
        original_paths = list(self.pathMemo)
        original_paths.sort(key=lambda path: len(path), reverse=True)
        paths = []
        for i in range(len(original_paths)):
            flag = True
            for j in range(i+1, len(original_paths)):
                if original_paths[i].startswith(original_paths[j]):
                    flag = False
                    break
            if flag:
                paths.append(original_paths[i])
        return paths

    def closeEvent(self, event):
        event.accept()
        if self.closeCallback is not None:
            rootDirs = self.getIndependentPaths()
            localStorage.save(StorageKey.RootDirs, rootDirs)
            self.closeCallback(rootDirs)