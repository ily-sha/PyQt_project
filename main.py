import sys
import io
import os
import geojson
import folium
import folium.plugins
import json
import country_view, config_country
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sqlite3
import PyQt5
from PyQt5.QtWebEngineWidgets import QWebEngineView

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Карта путешествиника')
        self.initView()

    def initView(self):
        self.horizLayout = QHBoxLayout(self)
        self.tabwidget = QTabWidget(self)
        verticalLayout = QVBoxLayout(self)
        self.btn = QPushButton("Пополнить список стран")
        self.btn.clicked.connect(self.openDialog)
        verticalLayout.addWidget(self.btn, 1)
        verticalLayout.addWidget(self.tabwidget, 3)
        self.listViewVisited = QListWidget(self)
        self.listViewVisited.setSpacing(2)
        self.listViewVisited.itemClicked.connect(self.onClicked)
        self.listViewVisited.setMinimumWidth(self.listViewVisited.sizeHintForColumn(5))
        self.tabwidget.addTab(self.listViewVisited, "Посещенные страны")
        self.listViewDream = QListWidget(self)
        self.listViewDream.setSpacing(2)
        self.listViewDream.itemDoubleClicked.connect(self.double_click)
        self.listViewDream.itemClicked.connect(self.onClicked)
        self.tabwidget.addTab(self.listViewDream, "Планируемые страны")
        self.updateListView()
        self.horizLayout.addLayout(verticalLayout, 1)
        self.createMap()

    def double_click(self, item):
        text = item.text()
        # двоной клиk переносить страну в посещенные
        try:
            self.country.close()
        except AttributeError:
            pass
        sqlite_connection = sqlite3.connect('db.sqlite')
        cursor = sqlite_connection.cursor()
        dream = """SELECT * FROM Dream WHERE Country = ?"""
        dream = cursor.execute(dream, (text, )).fetchall()[0]
        delete = """DELETE from Dream WHERE Country = ?"""
        delete = cursor.execute(delete, (text, )).fetchall()
        visited = """INSERT INTO Visited VALUES (?, ?, ?, ?, ?)"""
        cursor.execute(visited, (dream[0], dream[1], '', dream[2], dream[3]))
        sqlite_connection.commit()
        cursor.close()
        self.updateListView()
        obj = json.load(open("dream.json"))
        for i in obj["features"]:
            if i["properties"]["name"] == text:
                arr = obj["features"]
                del arr[arr.index(i)]
                break
        with open("dream.json", "w") as f:
            json.dump(obj, f)
        obj2 = json.load(open("visited.json"))
        obj2["features"].append(i)
        with open("visited.json", "w") as f:
            json.dump(obj2, f)
        self.updateMap()


    def onClicked(self, item):
        geojson = self.parse(country=item.text(), toFind=True, item=None)
        if self.tabwidget.currentIndex() == 0:
            self.country = country_view.CountryView("vis", geojson, item.text(), self)
            self.country.setGeometry(self.width() // 5, self.height() // 5, self.width() // 5 * 3,
                                     self.height() // 10 * 7)
        else:
            self.country = country_view.CountryView("dre", geojson, item.text(), self)
            self.country.setGeometry(self.width() // 5, self.height() // 5, self.width() // 10 * 5,
                                     self.height() // 10 * 7)
        self.country.show()


    def add_items(self, texts, t):
        if t == 1:
            self.listViewVisited.clear()
        else:
            self.listViewDream.clear()
        for text in texts:
            item = QListWidgetItem(text)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            size = QSize()
            size.setHeight(30)
            size.setWidth(10)
            item.setSizeHint(size)
            item.setFont(QFont("Microsoft Sans Serif"))
            if t == 1:
                self.listViewVisited.addItem(item)
            else:
                self.listViewDream.addItem(item)


    def updateListView(self):
        sqlite_connection = sqlite3.connect('db.sqlite')
        cursor = sqlite_connection.cursor()
        self.add_items([i[0] for i in cursor.execute("""SELECT * FROM Visited""").fetchall()], 1)
        self.add_items([i[0] for i in cursor.execute("""SELECT * FROM Dream""").fetchall()], 0)
        cursor.close()


    def createMap(self):
        # ,
        self.map = folium.Map(location=[50, 35], tiles='cartodbpositron', attr='map', zoom_start=3, control_scale=True)
        folium.GeoJson("allCountry.json", name="Countries",
                       style_function=lambda x: {'fillColor': 'lightblue', 'color': 'black', 'weight': 1,
                                                 'fillOpacity': 0}, highlight_function=lambda x: {'fillOpacity': 0},
                       tooltip=folium.features.GeoJsonTooltip(fields=['name']),
                       popup=folium.GeoJsonPopup(fields=["name"])).add_to(self.map)

        self.dream = folium.plugins.FeatureGroupSubGroup(self.map, 'Планируемые страны')
        self.map.add_child(self.dream)
        self.visited = folium.plugins.FeatureGroupSubGroup(self.map, 'Посещенные страны')
        self.map.add_child(self.visited)
        try:
            self.dreamCountry = folium.GeoJson("dream.json", style_function=lambda x: {'fillColor': 'orange',
                                                'color': 'black', 'weight': 1, 'fillOpacity': 0.5},
                                               highlight_function=lambda x: {'fillOpacity': 15},
                                               tooltip=folium.features.GeoJsonTooltip(fields=['name'],
                                                aliases=['County: '])).add_to(self.dream)
        except IndexError:
            pass
        try:
            self.visitedCounty = folium.GeoJson("visited.json", style_function=lambda x: {'fillColor': 'blue',
                                                'color': 'black', 'weight': 1, 'fillOpacity': 0.5},
                                                highlight_function=lambda x: {'fillOpacity': 15},
                                                tooltip=folium.features.GeoJsonTooltip(fields=['name'],
                                                aliases=['County: '])).add_to(self.visited)
        except IndexError:
            pass
        folium.LayerControl(collapsed=False).add_to(self.map)
        data = io.BytesIO()
        self.map.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        self.horizLayout.addWidget(webView, 4)
        self.setLayout(self.horizLayout)


    def openDialog(self):
        self.dialog = config_country.DialogView(self)
        self.dialog.show()


    def parse(self, country, item, toFind=False):
        self.isCountryFind = False
        with open("allCountry.json") as p:
            jsonFile = geojson.load(p)
        for i in jsonFile["features"]:
            if i["properties"]["name"] == country:
                self.isCountryFind = True
                break
        if not self.isCountryFind:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Warning!")
            dlg.setText("Название страны написано неверно")
            button = dlg.exec()
            return False
        else:
            if toFind:
                return i
            else:
                self.parseCurrentCountry(item, i)
                return True


    def parseCurrentCountry(self, item, i):
        if item == 1:
            try:
                with open("visited.json") as f:
                    visitedJson = json.load(f)
                    visitedJson["features"].append(i)
            except json.JSONDecodeError as jse:
                print(jse.msg)
            with open("visited.json", "w") as f:
                json.dump(visitedJson, f)
        else:
            try:
                with open("dream.json") as f:
                    dreamJson = json.load(f)
                    dreamJson["features"].append(i)
            except json.JSONDecodeError as jse:
                print(jse.msg)
            with open("dream.json", "w") as f:
                json.dump(dreamJson, f)
        self.updateMap()


    def updateMap(self):
        self.createMap()
        self.horizLayout.itemAt(1).widget().deleteLater()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myApp = MyApp()
    myApp.showMaximized()
    sys.exit(app.exec_())


