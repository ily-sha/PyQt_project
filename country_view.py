from PyQt5.QtWidgets import *
import main
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QIcon
import sqlite3
import io
import folium
import json
import os
import config_country
import main
from PyQt5.QtWebEngineWidgets import QWebEngineView

class Photo(QWidget):
    def __init__(self, pzz):
        super(Photo, self).__init__()
        self.label = QLabel(self)
        self.label.setPixmap(pzz)
        self.label.move(0, 0)


class CountryView(QWidget):
    def __init__(self, item, geojson, name, arg):
        super().__init__()
        self.arg = arg
        self.item = item
        self.geojson = geojson
        self.name = name
        self.init()

    def init(self):
        self.setWindowTitle("О стране")
        self.horizLayout = QHBoxLayout(self)
        if self.item == "vis":
            cont = QVBoxLayout(self)
            self.listViewOfPhoto = QListWidget(self)
            self.listViewOfPhoto.itemClicked.connect(self.onClickedItemQ)
            cont.addWidget(self.listViewOfPhoto)
            self.btnAddPhoto = QPushButton("Добавить фотографии")
            self.btnAddPhoto.clicked.connect(self.addPhoto)
            cont.addWidget(self.btnAddPhoto)
            self.horizLayout.addLayout(cont, 3)
        self.comment = QTextEdit()
        self.comment.setReadOnly(True)
        self.comment.setText(self.readBdAndFullListView())
        buttonLayout = QVBoxLayout(self)
        self.btnDelete = QPushButton("Удалить страну из списка")
        self.btnDelete.clicked.connect(self.deleteCountry)
        self.btnUpadateText = QPushButton("Редактировать комментaрий")
        self.btnUpadateText.clicked.connect(self.updateText)
        self.btnSave = QPushButton("Сохранить")
        self.btnSave.clicked.connect(self.save)
        self.btnOk = QPushButton("Ок")
        self.btnOk.clicked.connect(self.okPressed)
        buttonLayout.addWidget(self.btnDelete)
        buttonLayout.addWidget(self.btnUpadateText)
        buttonLayout.addWidget(self.btnSave)
        buttonLayout.addWidget(self.btnOk)
        self.horLay = QHBoxLayout(self)
        self.horLay.addWidget(self.comment, 5)
        self.horLay.addLayout(buttonLayout, 2)
        self.createMap()

    def onClickedItemQ(self, item):
        inswx = self.listViewOfPhoto.currentRow()
        pixmax = self.arrOfSizePhoto[inswx]
        if pixmax.size().width() > self.arg.width() or pixmax.size().height() > self.arg.height():
            pixmax = pixmax.scaled(self.arg.width() - 25, self.arg.height() - 25, Qt.KeepAspectRatio)
        self.photoWdget = Photo(pixmax)
        self.photoWdget.setGeometry(0, 0, pixmax.size().width(), pixmax.size().height())
        self.photoWdget.show()

    def createMap(self):
        self.map = folium.Map(zoom_start=6, tiles='cartodbpositron', control_scale=True)
        folium.GeoJson(data=self.geojson, style_function=lambda x: {'fillColor': '#00FF7F', 'color': 'black',
                                                                    'weight': 1, 'fillOpacity': 0.5},).add_to(self.map)
        data = io.BytesIO()
        self.map.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        vertical = QVBoxLayout(self)
        vertical.addWidget(webView, 3)
        vertical.addLayout(self.horLay, 1)
        self.horizLayout.addLayout(vertical, 7)
        self.setLayout(self.horizLayout)

    def deleteCountry(self):
        sqlite_connection = sqlite3.connect('db.sqlite')
        cursor = sqlite_connection.cursor()
        if self.item == "vis":
            sqlite_insert_blob_query = """DELETE from Visited WHERE Country = ?"""
            obj = json.load(open("visited.json"))
        else:
            sqlite_insert_blob_query = """DELETE from Dream WHERE Country = ?"""
            obj = json.load(open("dream.json"))
        cursor.execute(sqlite_insert_blob_query, (self.name, ))
        sqlite_connection.commit()
        cursor.close()
        main.MyApp.updateListView(self.arg)
        for i in obj["features"]:
            if i["properties"]["name"] == self.name:
                arr = obj["features"]
                del arr[arr.index(i)]
                break
        if self.item == "vis":
            with open("visited.json", "w") as f:
                json.dump(obj, f)
        else:
            with open("dream.json", "w") as f:
                json.dump(obj, f)
        main.MyApp.updateMap(self.arg)
        self.close()

    def updateText(self):
        self.comment.setReadOnly(False)

    def save(self):
        sqlite_connection = sqlite3.connect('db.sqlite')
        cursor = sqlite_connection.cursor()
        if self.item != "vis":
            sqlite_insert_blob_query = """UPDATE Dream SET Comment = ? WHERE Country = ?"""
        else:
            sqlite_insert_blob_query = """UPDATE Visited SET Comment = ? WHERE Country = ?"""
        cursor.execute(sqlite_insert_blob_query, (self.comment.toPlainText(), self.name))
        sqlite_connection.commit()
        cursor.close()

    def okPressed(self):
        self.close()

    def readBdAndFullListView(self):
        self.arrOfSizePhoto = []
        try:
            sqlite_connection = sqlite3.connect('db.sqlite')
            cursor = sqlite_connection.cursor()
            if self.item == "vis":
                pyk = """SELECT * FROM Visited WHERE Country = ?"""
                res = cursor.execute(pyk, (self.name,)).fetchall()
                ids = res[0][2]
                if len(ids) != 0:
                    for i in ids.split(";"):
                        photo = """SELECT photo FROM Photo WHERE id= ?"""
                        resPhoto = cursor.execute(photo, (int(i), )).fetchall()[0][0]
                        photo_path = os.path.join("db_data.jpg")
                        with open(photo_path, 'wb') as file:
                            file.write(resPhoto)
                        icon = QIcon(photo_path)
                        px = QPixmap(photo_path)
                        self.arrOfSizePhoto.append(px)
                        self.listViewOfPhoto.setIconSize(QSize(206.5, 200))
                        item = QListWidgetItem("")
                        item.setIcon(icon)
                        self.listViewOfPhoto.addItem(item)
                    cursor.close()
            else:
                pyk = """SELECT * FROM Dream WHERE Country = ?"""
                res = cursor.execute(pyk, (self.name,)).fetchall()
        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)
        return res[0][1]

    def addPhoto(self):
        try:
            self.photoChanged = True
            self.original = QFileDialog.getOpenFileNames(self, 'Выбрать картинки', '')[0]
            sqlite_connection = sqlite3.connect('db.sqlite')
            cursor = sqlite_connection.cursor()
            oldData = """SELECT PhotoId FROM Visited WHERE Country = ?"""
            oldDatas = cursor.execute(oldData, (self.name, )).fetchall()[0][0]
            sqlite_insert_blob_query = """UPDATE Visited SET PhotoId = ?
                             WHERE Country = ?"""
            if len(oldDatas) == 0:
                rangeOfPhoto = config_country.DialogView.convert_to_binary_data(self, self.original)
            else:
                rangeOfPhoto = oldDatas + ";" + config_country.DialogView.convert_to_binary_data(self, self.original)
            cursor.execute(sqlite_insert_blob_query, (rangeOfPhoto, self.name))
            sqlite_connection.commit()
            self.readBdAndFullListView()
        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)




