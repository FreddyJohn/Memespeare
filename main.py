import os
import sys
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *
import memeLogic
from dotenv import load_dotenv


class Meme(QLabel):
    def __int__(self, parent):
        super().__init__(parent)
        self.parent = parent


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
        button.clicked.connect(self.clickme)

        self.textedit = QTextEdit(self)
        self.textedit.setGeometry(0, 0, 400, 30)
        self.setAcceptDrops(True)
        self.show()

    def dragEnterEvent(self, e):
        print("drag enter event")
        e.accept()

    def dropEvent(self, e):
        image_path = e.mimeData().text()
        meme_tags = self.getText()
        memeLogic.insert(image_path, meme_tags)

    def clear_memes(self):
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

    def clickme(self):
        keywords = self.textedit.toPlainText()
        self.clear_memes()
        memes = memeLogic.get_memes_from_wasabi(memeLogic.find_memes([keywords]))
        for meme in memes:
            label = QLabel(self)
            pixmap = QPixmap(os.path.abspath(meme))
            label.setPixmap(pixmap)
            self.layout.addWidget(label)

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
