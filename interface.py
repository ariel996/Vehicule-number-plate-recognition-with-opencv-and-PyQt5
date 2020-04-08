from PyQt5.QtGui import QPixmap, QImage

from listdata import Ui_list_dialog
from ui_main import Ui_MainWindow
# from resultat import Ui_Dialog
import addDialog
from editDialog import Ui_Dialog

import numpy as np
import imutils
import os

import DetectChars
import DetectPlates
import PossiblePlate

from PyQt5.QtCore import QFile, QFileInfo, QTextStream
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QTableWidgetItem, QFileDialog, QLabel

import cv2 #librairies for image processing

import sqlite3 #librairy for SQLite database

conn = sqlite3.connect('vnpr.db')
curs = conn.cursor()
curs.execute('CREATE TABLE IF NOT EXISTS vehicle(plate TEXT, mark TEXT, model TEXT, colour TEXT, year TEXT, ownerName TEXT, ownerCNI TEXT, ownerAddress TEXT) ')

# module level variables
SCALAR_BLACK = (0.0, 0.0, 0.0)
SCALAR_WHITE = (255.0, 255.0, 255.0)
SCALAR_YELLOW = (0.0, 255.0, 255.0)
SCALAR_GREEN = (0.0, 255.0, 0.0)
SCALAR_RED = (0.0, 0.0, 255.0)

showSteps = False

class Interface(QMainWindow):

    def __init__(self, parent=None):
        super(Interface, self).__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.initialisation()

    def initialisation(self):
        self.show()
        self.display = listData()
        #self.result = ResultatDialog()
        #self.ui.list_data_button.clicked.connect(self.display.Init_Ui)
        self.ui.exploreButton.clicked.connect(self.Load_picture)
        self.ui.launch_button.clicked.connect(self.launchCamera)

    def launchCamera(self):
        url = 'http://192.168.1.113:8080/video'
        file = 'LicPlateImages/video3.mp4'
        fileName, _ = QFileDialog.getOpenFileName(None, 'Open Video','', "All video files (*.mp4);; Images Files (*.mp4)")
        cap = cv2.VideoCapture(fileName)
        count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if ret == True:
                cv2.imshow('VNPR', frame)
                cv2.imwrite("images/frame%d.jpg" % count, frame)
                count = count + 1
                if cv2.waitKey(10) & 0xFF == ord('q'): # 10 milliseconds and 'q' button press to quit the application
                    break
            else:
                break
        cap.release()
        cv2.destroyAllWindows()
        blnKNNTrainingSuccessful = DetectChars.loadKNNDataAndTrainKNN()  # attempt KNN training

        if blnKNNTrainingSuccessful == False:  # if KNN training was not successful
            print("\nerror: KNN traning was not successful\n")  # show error message
            return  # and exit program
        # end if
        imgOriginalScene1 = cv2.imread("images/frame%d.jpg"%(count - 1)) # open image
        imgOriginalScene = imutils.resize(imgOriginalScene1, width=500)
        if imgOriginalScene is None:  # if image was not read successfully
            print("\nerror: image not read from file \n\n")  # print error message to std out
            os.system("pause")  # pause so user can see error message
            return  # and exit program
        # end if
        listOfPossiblePlates = DetectPlates.detectPlatesInScene(imgOriginalScene)  # detect plates

        listOfPossiblePlates = DetectChars.detectCharsInPlates(listOfPossiblePlates)  # detect chars in plates

        cv2.imshow("imgOriginalScene", imgOriginalScene)  # show scene image

        if len(listOfPossiblePlates) == 0:  # if no plates were found
            print("\nno license plates were detected\n")  # inform user no plates were found
        else:  # else
            # if we get in here list of possible plates has at leat one plate

            # sort the list of possible plates in DESCENDING order (most number of chars to least number of chars)
            listOfPossiblePlates.sort(key=lambda possiblePlate: len(possiblePlate.strChars), reverse=True)

            # suppose the plate with the most recognized chars (the first plate in sorted by string length descending order) is the actual plate
            licPlate = listOfPossiblePlates[0]

            cv2.imshow("imgPlate", licPlate.imgPlate)  # show crop of plate and threshold of plate
            cv2.imshow("imgThresh", licPlate.imgThresh)

            if len(licPlate.strChars) == 0:  # if no chars were found in the plate
                print("\nno characters were detected\n\n")  # show message
                return  # and exit program
            # end if

            # drawRedRectangleAroundPlate(imgOriginalScene, licPlate)  # draw red rectangle around plate

            self.ui.result_label.setText(licPlate.strChars)

            # writeLicensePlateCharsOnImage(imgOriginalScene, licPlate)  # write license plate text on the image

            cv2.imshow("imgOriginalScene", imgOriginalScene)  # re-show scene image

            cv2.imwrite("imgOriginalScene.png", imgOriginalScene)  # write image out to file

            # selection of number plate from the database
            numPlate = str(licPlate.strChars)
            curs = conn.cursor()
            results = curs.execute("SELECT * FROM vehicle WHERE plate = '" + numPlate + "'")
            # ligne = results.fetchone()
            resultat = results.fetchall()
            for ligne in resultat:
                plate = ligne[0]
                mark = ligne[1]
                colour = ligne[2]
                assurance = ligne[3]
                technique = ligne[4]
                ownerName = ligne[5]
                ownerCNI = ligne[6]
                address = ligne[7]
                # self.result.show()
                if assurance == 'incorrect' or technique == 'incorrect':
                    QMessageBox.information(self, "VNPR SYSTEM",
                                            "You are not elligible to circulate. Pay you assurance fee and technical visit")
                else:
                    QMessageBox.information(self, "Vehicle Information", "Plate Number: " + plate + "\n"
                                            + "Mark: " + mark + "\n" + "Color: " + colour + "\n"
                                            + "Assurance: " + assurance + "\n" + "Technique: " + technique + "\n" + "Name: " + ownerName + "\n"
                                            + "CNI: " + ownerCNI + "\n" + "Address: " + address + "\n" + "BALANCE:  500 F CFA")
            if not resultat:
                QMessageBox.information(self, "WARNING", "Data does not match our record in the database")

        # end if else

        cv2.waitKey(0)  # hold windows open until user presses a key

        return

    # end execution

    def Load_picture(self):
        fileName, _ = QFileDialog.getOpenFileName(None, 'Open Image','', "All image files (*.jpg, *.jpeg, *.png);; Images Files (*.jpg)")
        if fileName:
            image = QImage(fileName)
            if image.isNull():
                QMessageBox.information(self,"Image viewer", "cannot load %s." %fileName)
                return
            self.ui.label_image.setPixmap(QPixmap.fromImage(image))
            # self.ui.execute_button.clicked.connect(self.execution)
            # print(fileName)
            blnKNNTrainingSuccessful = DetectChars.loadKNNDataAndTrainKNN()  # attempt KNN training

            if blnKNNTrainingSuccessful == False:  # if KNN training was not successful
                print("\nerror: KNN traning was not successful\n")  # show error message
                return  # and exit program
            # end if

            imgOriginalScene1 = cv2.imread(fileName)  # open image
            imgOriginalScene = imutils.resize(imgOriginalScene1, width=500)
            if imgOriginalScene is None:  # if image was not read successfully
                print("\nerror: image not read from file \n\n")  # print error message to std out
                os.system("pause")  # pause so user can see error message
                return  # and exit program
            # end if
            listOfPossiblePlates = DetectPlates.detectPlatesInScene(imgOriginalScene)  # detect plates

            listOfPossiblePlates = DetectChars.detectCharsInPlates(listOfPossiblePlates)  # detect chars in plates

            cv2.imshow("imgOriginalScene", imgOriginalScene)  # show scene image

            if len(listOfPossiblePlates) == 0:  # if no plates were found
                print("\nno license plates were detected\n")  # inform user no plates were found
            else:  # else
                # if we get in here list of possible plates has at leat one plate

                # sort the list of possible plates in DESCENDING order (most number of chars to least number of chars)
                listOfPossiblePlates.sort(key=lambda possiblePlate: len(possiblePlate.strChars), reverse=True)

                # suppose the plate with the most recognized chars (the first plate in sorted by string length descending order) is the actual plate
                licPlate = listOfPossiblePlates[0]

                cv2.imshow("imgPlate", licPlate.imgPlate)  # show crop of plate and threshold of plate
                cv2.imshow("imgThresh", licPlate.imgThresh)

                if len(licPlate.strChars) == 0:  # if no chars were found in the plate
                    print("\nno characters were detected\n\n")  # show message
                    return  # and exit program
                # end if

                # drawRedRectangleAroundPlate(imgOriginalScene, licPlate)  # draw red rectangle around plate

                self.ui.result_label.setText(licPlate.strChars)

                # writeLicensePlateCharsOnImage(imgOriginalScene, licPlate)  # write license plate text on the image

                cv2.imshow("imgOriginalScene", imgOriginalScene)  # re-show scene image

                cv2.imwrite("imgOriginalScene.png", imgOriginalScene)  # write image out to file

                # selection of number plate from the database
                # conn = sqlite3.connect('vnpr.db')
                numPlate = str(licPlate.strChars)
                curs = conn.cursor()
                results = curs.execute("SELECT * FROM vehicle WHERE plate = '" + numPlate + "'")
                #ligne = results.fetchone()
                resultat = results.fetchall()
                for ligne in resultat:
                    plate = ligne[0]
                    mark = ligne[1]
                    colour = ligne[2]
                    assurance = ligne[3]
                    technique = ligne[4]
                    ownerName = ligne[5]
                    ownerCNI = ligne[6]
                    address = ligne[7]
                    #self.result.show()
                    if assurance == 'incorrect' or technique == 'incorrect':
                        QMessageBox.information(self, "VNPR", "You are not elligible to circulate. Pay you assurance fee and technical visit")
                    else:
                        conn.execute("UPDATE vehicle SET balance = 500.00 WHERE plate = '" + plate + "'")
                        conn.commit()
                        somme = conn.execute("SELECT SUM(balance) FROM vehicle")
                        self.ui.lcdNumber_amount.display('500 F')
                        QMessageBox.information(self, "Vehicle Information", "Plate Number: " + plate + "\n"
                                            + "Mark: " + mark + "\n" + "Color: " + colour + "\n"
                                            + "Assurance: " + assurance + "\n" + "Technique:" + technique + "\n" + "Name: " + ownerName + "\n"
                                            + "CNI: " + ownerCNI + "\n" + "Address: " + address + "\n" + "BALANCE:  500 F CFA")
                if not resultat:
                        QMessageBox.information(self, "WARNING", "Data does not match our record in the database")

            # end if else

            cv2.waitKey(0)  # hold windows open until user presses a key

            return
        # end execution


    def drawRedRectangleAroundPlate(imgOriginalScene, licPlate):

        p2fRectPoints = cv2.boxPoints(licPlate.rrLocationOfPlateInScene)            # get 4 vertices of rotated rect

        cv2.line(imgOriginalScene, tuple(p2fRectPoints[0]), tuple(p2fRectPoints[1]), SCALAR_RED, 2)         # draw 4 red lines
        cv2.line(imgOriginalScene, tuple(p2fRectPoints[1]), tuple(p2fRectPoints[2]), SCALAR_RED, 2)
        cv2.line(imgOriginalScene, tuple(p2fRectPoints[2]), tuple(p2fRectPoints[3]), SCALAR_RED, 2)
        cv2.line(imgOriginalScene, tuple(p2fRectPoints[3]), tuple(p2fRectPoints[0]), SCALAR_RED, 2)
    # end function

    def writeLicensePlateCharsOnImage(imgOriginalScene, licPlate):
        ptCenterOfTextAreaX = 0                             # this will be the center of the area the text will be written to
        ptCenterOfTextAreaY = 0

        ptLowerLeftTextOriginX = 0                          # this will be the bottom left of the area that the text will be written to
        ptLowerLeftTextOriginY = 0

        sceneHeight, sceneWidth, sceneNumChannels = imgOriginalScene.shape
        plateHeight, plateWidth, plateNumChannels = licPlate.imgPlate.shape

        intFontFace = cv2.FONT_HERSHEY_SIMPLEX                      # choose a plain jane font
        fltFontScale = float(plateHeight) / 30.0                    # base font scale on height of plate area
        intFontThickness = int(round(fltFontScale * 1.5))           # base font thickness on font scale

        textSize, baseline = cv2.getTextSize(licPlate.strChars, intFontFace, fltFontScale, intFontThickness)        # call getTextSize

                # unpack roatated rect into center point, width and height, and angle
        ( (intPlateCenterX, intPlateCenterY), (intPlateWidth, intPlateHeight), fltCorrectionAngleInDeg ) = licPlate.rrLocationOfPlateInScene

        intPlateCenterX = int(intPlateCenterX)              # make sure center is an integer
        intPlateCenterY = int(intPlateCenterY)

        ptCenterOfTextAreaX = int(intPlateCenterX)         # the horizontal location of the text area is the same as the plate

        if intPlateCenterY < (sceneHeight * 0.75):                                                  # if the license plate is in the upper 3/4 of the image
            ptCenterOfTextAreaY = int(round(intPlateCenterY)) + int(round(plateHeight * 1.6))      # write the chars in below the plate
        else:                                                                                       # else if the license plate is in the lower 1/4 of the image
            ptCenterOfTextAreaY = int(round(intPlateCenterY)) - int(round(plateHeight * 1.6))      # write the chars in above the plate
        # end if

        textSizeWidth, textSizeHeight = textSize                # unpack text size width and height

        ptLowerLeftTextOriginX = int(ptCenterOfTextAreaX - (textSizeWidth / 2))           # calculate the lower left origin of the text area
        ptLowerLeftTextOriginY = int(ptCenterOfTextAreaY + (textSizeHeight / 2))          # based on the text area center, width, and height

                # write the text on the image
        cv2.putText(imgOriginalScene, licPlate.strChars, (ptLowerLeftTextOriginX, ptLowerLeftTextOriginY), intFontFace, fltFontScale, SCALAR_YELLOW, intFontThickness)
    # end function

class listData(QDialog):
    def __init__(self, parent=None):
        super(listData, self).__init__(parent)

        self.ui = Ui_list_dialog()
        self.ui.setupUi(self)
        self.Load_Database()

        self.Init_Ui()

    def Init_Ui(self):
        self.show()
        self.ui.add_button.clicked.connect(self.Show_Add_Dialog)
        self.ui.delete_button.clicked.connect(self.Delete_Data)
        self.ui.refresh_button.clicked.connect(self.Load_Database)
        self.ui.search_button.clicked.connect(self.searchplate)

    def Show_Add_Dialog(self):
        self.adding = AddDialog()
        self.adding.pushButton.clicked.connect(self.Add_Data)
        self.adding.exec_()

    def Add_Data(self):
        plate = self.adding.lineEdit.text()
        mark = self.adding.lineEdit_2.text()
        colour = self.adding.lineEdit_3.text()
        assurance = self.adding.lineEdit_4.text()
        technique = self.adding.lineEdit_5.text()
        ownerName = self.adding.lineEdit_6.text()
        ownerCNI = self.adding.lineEdit_7.text()
        ownerAddress = self.adding.lineEdit_8.text()
        try:
            conn.execute(
                'INSERT INTO vehicle(plate, mark, colour, assurance, technique, ownerName, ownerCNI, ownerAddress) VALUES (?,?,?,?,?,?,?,?)',
                (plate, mark, colour, assurance, technique, ownerName, ownerCNI, ownerAddress))
            conn.commit()
            QMessageBox.about(self, "Success", "Data inserted successfully")
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
                assurance = data[3]
                technique = data[4]
                ownerName = data[5]
                ownerCNI = data[6]
                ownerAddress = data[7]
                curs.execute(
                    'DELETE FROM vehicle WHERE plate=? AND mark=? AND colour=? AND assurance=? AND technique=? AND ownerName=? AND ownerCNI=? AND ownerAddress=?',
                    (plate, mark, colour, assurance, technique, ownerName, ownerCNI, ownerAddress))
                conn.commit()
                self.Load_Database()

    def searchplate(self):
        searchnum = ""
        searchnum = self.ui.lineEdit.text()
        try:
            self.conn = sqlite3.connect("vnpr.db")
            self.c = self.conn.cursor()
            result = self.c.execute("SELECT * FROM vehicle WHERE plate="+str(searchnum))
            row = result.fetchone()
            searchresult = "Plate: "+str(row[0])+'\n'+"Name: "+str(row[5])+'\n'+"CNI: "+str(row[6])+'\n'+"Mark: "+str(row[1])
            QMessageBox.information(QMessageBox(),'Successfull', searchresult)
            self.conn.commit()
            self.c.close()
            self.conn.close()
        except Exception:
            QMessageBox.warning(QMessageBox(), 'Error', 'Could not Find number plate from the database.')

    def Load_Database(self):
        while self.ui.tableWidget.rowCount() > 0:
            self.ui.tableWidget.removeRow(0)
        conn = sqlite3.connect('vnpr.db')
        content = 'SELECT * FROM vehicle'
        res = curs.execute(content) #conn.execute(content)
        for row_index, row_data in enumerate(res):
            self.ui.tableWidget.insertRow(row_index)
            for colm_index, colm_data in enumerate(row_data):
                self.ui.tableWidget.setItem(row_index, colm_index, QTableWidgetItem(str(colm_data)))
        self.ui.lcdNumber.display(str(self.ui.tableWidget.rowCount()))
        # conn.close()
        return


class AddDialog(QDialog, addDialog.Ui_Dialog):
    def __init__(self, parent=None):
        super(AddDialog, self).__init__(parent)
        self.setupUi(self)


class EditDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(EditDialog, self).__init__((parent))
        self.setupUi(self)

# class ResultatDialog(QDialog, Ui_Dialog):
#     def __init__(self, parent=None):
#         super(ResultatDialog, self).__init__((parent))
#         self.setupUi(self)


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    interface = Interface()
    interface.show()

    sys.exit(app.exec_())