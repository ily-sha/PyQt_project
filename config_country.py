import main
import sqlite3

import PyQt5
from PyQt5.QtWidgets import QWidget

class Photo(QWidget):
    def __init__(self, pzz):
        super(Photo, self).__init__()
        self.label = QLabel(self)
        self.label.setPixmap(pzz)
        self.label.move(0, 0)


class DialogView(QWidget):
    def __init__(self, arg):
        super().__init__()
        self.arg = arg
        self.init()

    def init(self):
        self.setGeometry(100, 100, 500, 500)
        self.setWindowTitle("Добавить страну")
        cenrtral = PyQt5.QtWidgets.QVBoxLayout(self)
        self.cenrtral2 = PyQt5.QtWidgets.QGridLayout(self)
        self.lineEdit = PyQt5.QtWidgets.QLineEdit()
        self.lineEdit.setToolTip("Напишите страну")
        self.tabwidgetDialog = PyQt5.QtWidgets.QTabWidget(self)
        self.dreamTextView = PyQt5.QtWidgets.QTextEdit(self)
        self.calendarView = PyQt5.QtWidgets.QCalendarWidget(self)
        self.original = None
        #  клик!!!!!!
        self.calendarView.clicked.connect(self.eventClick)
        self.calendarView0 = PyQt5.QtWidgets.QCalendarWidget(self)
        self.calendarView0.clicked.connect(self.eventClick)
        tab1 = PyQt5.QtWidgets.QWidget()
        tab1.layout = PyQt5.QtWidgets.QVBoxLayout(self)
        tab1.layout.addWidget(self.dreamTextView)
        tab1.layout.addWidget(self.calendarView0)
        tab1.setLayout(tab1.layout)
        self.tabwidgetDialog.addTab(tab1, "Планируемые страны")
        self.dreamTextView.setToolTip("Напишите ваши ожидания, где планируете побывать")
        tab2 = PyQt5.QtWidgets.QWidget()
        tab2.layout = PyQt5.QtWidgets.QVBoxLayout(self)
        self.visitedTextView = PyQt5.QtWidgets.QTextEdit(self)
        self.visitedTextView.setToolTip("Напишите ваши впечатления, где побывали, располагались, куда ездили")
        self.btnOfPhoto = PyQt5.QtWidgets.QPushButton("Добавить фотографии")
        self.btnOfPhoto.clicked.connect(self.openPhoto)
        tab2.layout.addWidget(self.visitedTextView)
        tab2.layout.addWidget(self.calendarView)
        tab2.layout.addWidget(self.btnOfPhoto)
        tab2.setLayout(tab2.layout)
        self.tabwidgetDialog.addTab(tab2, "Посещенные страны")
        self.bntOk = PyQt5.QtWidgets.QPushButton("Ok")
        self.bntOk.clicked.connect(self.okPressed)
        self.bntClose = PyQt5.QtWidgets.QPushButton("Close")
        self.bntClose.clicked.connect(self.closePressed)
        self.cenrtral2.addWidget(self.lineEdit, 0, 0)
        self.cenrtral2.addWidget(self.tabwidgetDialog, 1, 0)
        lay = PyQt5.QtWidgets.QHBoxLayout()
        lay.addWidget(self.bntClose)
        lay.addWidget(self.bntOk)
        cenrtral.addLayout(self.cenrtral2)
        cenrtral.addLayout(lay)
        self.setLayout(cenrtral)
        self.arrOfData = []

    def okPressed(self):
        text = self.lineEdit.text()
        if self.tabwidgetDialog.currentIndex() == 0:
            bigData = self.dreamTextView.toPlainText()
            if main.MyApp.parse(self.arg, text, 0):
                self.insert_data(text, bigData, data=self.arrOfData)
        else:
            bigData = self.visitedTextView.toPlainText()
            if main.MyApp.parse(self.arg, text, 1):
                self.insert_data(text, bigData, photos=self.original, data=self.arrOfData)
        self.close()

    def closePressed(self):
        self.close()

    def openPhoto(self):
        if self.original == None:
            self.original = PyQt5.QtWidgets.QFileDialog.getOpenFileNames(self, 'Выбрать картинки', '')[0]
            self.count = 0
            self.horLay = PyQt5.QtWidgets.QHBoxLayout()
        else:
            self.original.extend(PyQt5.QtWidgets.QFileDialog.getOpenFileNames(self, 'Выбрать картинки', '')[0])

        try:
            while self.count < 3:
                pixmap = PyQt5.QtGui.QPixmap(self.original[self.count])
                pixmap = pixmap.scaled(125, 125)
                label = PyQt5.QtWidgets.QLabel()
                label.setPixmap(pixmap)
                self.horLay.addWidget(label)
                self.count += 1
            self.cenrtral2.addLayout(self.horLay, 2, 0)
        except IndexError:
            self.cenrtral2.addLayout(self.horLay, 2, 0)
            pass


    def eventClick(self):
        if len(self.arrOfData) < 2:
            if self.tabwidgetDialog.currentIndex() == 0:
                self.arrOfData.append(self.calendarView0.selectedDate().toString("yyyy-MM-dd"))
            else:
                self.arrOfData.append(self.calendarView.selectedDate().toString("yyyy-MM-dd"))

    def convert_to_binary_data(self, filenames):
        try:
            sqlite_connection = sqlite3.connect('db.sqlite')
            cursor = sqlite_connection.cursor()
            result = cursor.execute("""SELECT * FROM Photo""").fetchall()
            if len(result) == 0:
                result = 0
            else:
                result = len(result)
            sqlite_insert_blob_query = """INSERT INTO Photo (photo) VALUES (?)"""
            for filename in filenames:
                with open(filename, 'rb') as file:
                    blob_data = file.read()
                data_tuple = (blob_data, )
                cursor.execute(sqlite_insert_blob_query, data_tuple)
            sqlite_connection.commit()
            if len(filenames) == 1:
                return str(result + 1)
            else:
                return ";".join(list(map(lambda x: x, [str(i) for i in range(result + 1, 1 + result + len(filenames))])))
        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def insert_data(self, name, comment, photos=None, data=None):
        try:
            sqlite_connection = sqlite3.connect('db.sqlite')
            cursor = sqlite_connection.cursor()
            if self.tabwidgetDialog.currentIndex() == 0:
                sqlite_insert_blob_query = """INSERT INTO Dream (Country, Comment, StartTravel, FinishTravel) 
                VALUES (?, ?, ?, ?)"""
                if len(data) != 0:
                    data_tuple = (name, comment, data[0], data[1])
                else:
                    data_tuple = (name, comment, None, None)
            else:
                sqlite_insert_blob_query = """INSERT INTO Visited (Country, Comment, PhotoId, StartTravel, FinishTravel)
                 VALUES (?, ?, ?, ?, ?)"""
                rangeOfPhoto = self.convert_to_binary_data(photos) if photos != None else ""
                # Преобразование данных в формат кортежа
                if len(data) != 0:
                    data_tuple = (name, comment, rangeOfPhoto, data[0], data[1])
                else:
                    data_tuple = (name, comment, rangeOfPhoto, None, None)
            cursor.execute(sqlite_insert_blob_query, data_tuple)
            sqlite_connection.commit()
            main.MyApp.updateListView(self.arg)
        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)
        except IndexError:
            pass
        finally:
            if sqlite_connection:
                sqlite_connection.close()


