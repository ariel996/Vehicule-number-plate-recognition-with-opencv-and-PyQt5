from registration import Ui_MainWindow
import addDialog
from editDialog import Ui_Dialog
from PyQt5.QtWidgets import QApplication,QDialog,QMainWindow,QMessageBox,QTableWidgetItem

import sqlite3

conn = sqlite3.connect('vnpr.db')
curs = conn.cursor()
curs.execute('CREATE TABLE IF NOT EXISTS vehicle(plate TEXT, mark TEXT, model TEXT, colour TEXT, year TEXT, ownerName TEXT, ownerCNI TEXT, ownerAddress TEXT) ')

class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)

        self.setupUi(self)
        self.Load_Database()

        self.Init_Ui()

    def Init_Ui(self):
        self.show()
        self.add_button.clicked.connect(self.Show_Add_Dialog)
        self.delete_button.clicked.connect(self.Delete_Data)

    def Show_Add_Dialog(self):
        self.adding = AddDialog()
        self.adding.pushButton.clicked.connect(self.Add_Data)
        self.adding.exec_()

    def Add_Data(self):
        plate = self.adding.lineEdit.text()
        mark = self.adding.lineEdit_2.text()
        model = self.adding.lineEdit_3.text()
        colour = self.adding.lineEdit_4.text()
        year = self.adding.lineEdit_5.text()
        ownerName = self.adding.lineEdit_6.text()
        ownerCNI = self.adding.lineEdit_7.text()
        ownerAddress = self.adding.lineEdit_8.text()
        try:
            conn.execute('INSERT INTO vehicle(plate, mark, colour, model, "year", ownerName, ownerCNI, ownerAddress) VALUES (?,?,?,?,?,?,?,?)', (plate,mark,colour,model,year,ownerName,ownerCNI,ownerAddress))
            conn.commit()
            QMessageBox.about(self,"Success","Data inserted successfully")
        except Exception as error:
            print(error)

    def Delete_Data(self):
        content = 'SELECT * FROM vehicle'
        res = curs.execute(content)
        for row in enumerate(res):
            if row[0] == self.tableWidget.currentRow():
                data = row[1]
                plate = data[0]
                mark = data[1]
                colour = data[2]
                model = data[3]
                year = data[4]
                ownerName = data[5]
                ownerCNI = data[6]
                ownerAddress = data[7]
                curs.execute('DELETE FROM vehicle WHERE plate=? AND mark=? AND colour=? AND model=? AND "year"=? AND ownerName=? AND ownerCNI=? AND ownerAddress=?', (plate,mark,colour,model,year,ownerName,ownerCNI,ownerAddress))
                conn.commit()
                self.Load_Database()


    def Load_Database(self):
        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow(0)
        conn = sqlite3.connect('vnpr.db')
        content = 'SELECT * FROM vehicle'
        res = conn.execute(content)
        for row_index, row_data in enumerate(res):
            self.tableWidget.insertRow(row_index)
            for colm_index, colm_data in enumerate(row_data):
                self.tableWidget.setItem(row_index,colm_index,QTableWidgetItem(str(colm_data)))
        self.lcdNumber.display(str(self.tableWidget.rowCount()))
        #conn.close()
        return

class AddDialog(QDialog,addDialog.Ui_Dialog):
    def __init__(self, parent=None):
        super(AddDialog, self).__init__(parent)
        self.setupUi(self)

class EditDialog(QDialog,Ui_Dialog):
    def __init__(self, parent=None):
        super(EditDialog, self).__init__((parent))
        self.setupUi(self)

app = QApplication([])
win = MainApp()
app.exec_()