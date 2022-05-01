import os
import sys
from PyQt5.QtGui import QPixmap, QDrag
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QMimeData, QUrl
import memeLogic
from dotenv import load_dotenv
from pathlib import Path


class Meme(QLabel):
    def __init__(self, parent, path):
        super().__init__(parent)
        self.path = os.path.abspath(path)
        pixmap = QPixmap(self.path)
        self.parent = parent
        self.setPixmap(pixmap)

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            meme_drop = QUrl(Path(self.path).as_uri())
            mime.setUrls([meme_drop])
            drag.setMimeData(mime)
            drag.exec_(Qt.MoveAction)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(os.getenv("APP_TITLE"))
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

        button = QPushButton("SEARCH", self)
        button.setGeometry(400, 0, 100, 30)
        button.clicked.connect(self.search_given_tags)

        self.textedit = QTextEdit(self)
        self.textedit.setGeometry(0, 0, 400, 30)
        # self.textedit.keyPressEvent(Qt.Key_Enter)

        self.setAcceptDrops(True)
        self.show()

    def dragEnterEvent(self, e):
        print("drag enter event")
        e.accept()

    def dropEvent(self, e):
        print("drop event")
        image_path = e.mimeData().text()
        meme_tags = self.getText()
        memeLogic.insert(image_path, meme_tags)

    def clear_memes(self):
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

    def search_given_tags(self):
        keywords = self.textedit.toPlainText()
        self.clear_memes()
        memes = memeLogic.get_memes_from_wasabi(memeLogic.find_memes([keywords]))
        for meme in memes:
            meme_widget = Meme(self, meme)
            self.layout.addWidget(meme_widget)

    def getText(self):
        text, okPressed = QInputDialog.getText(self, "Meme Tags", "Separate Tags with a comma:", QLineEdit.Normal, "")
        if okPressed and text != '':
            return text.split(',')


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    load_dotenv()
    memeLogic.create_db()
    App = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.excepthook = except_hook
    sys.exit(App.exec())
