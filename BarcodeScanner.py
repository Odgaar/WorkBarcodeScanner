"""
Barcode Scanner (Stregkode-scanner, in danish). This small programe function a bit like the windows snipping tool, in that it can snip a window and display an image.
However this program also scans the snip and displays a barcode label code, so that it dose not have to be read manueal from the screen. 
This aids in the work flow, since there is no need to fill in the barcode details manualy. 
Made by TMO 2022/07/13

"""

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, QObject, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QGroupBox
import tkinter as tk
from PIL import ImageGrab
import sys
from pyzbar import pyzbar
import cv2
import numpy as np
import qdarktheme

# Definere globale variable 
dataSignal = 0
dataRead = 0
dataType = None 
dataDirrection = None


QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

class Communicate(QObject):
    
    snip_saved = pyqtSignal()
# Classen that defindes the UI setup
class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        
        self.win_width = 380  # Size on window
        self.win_height = 250
        self.setGeometry(50, 50, self.win_width, self.win_height)
        self.setWindowTitle("Stregkode scanner")
      #  self.setFixedSize(QSize(self.win_width, self.win_height)) # Lock screen size so it cant be changed 
        self.initUI()
    
    def initUI(self):
        #Pressure button
        self.searchOpen = QPushButton(self)
        self.searchOpen.setText("Scan GTIN/EAN kode")
        self.searchOpen.move(15,80)
        self.searchOpen.setFixedSize(170,40)
        self.searchOpen.clicked.connect(self.snip_search_clicked) 
        
        
        #Notification box 
        self.notificationBox = QGroupBox("Status", self)
        self.notificationBox.move(10,135)
        self.notificationBox.setFixedSize(self.win_width-20,80)
        
        self.notificationText = QLabel(self)
        self.notificationText.move(20, 145)
        self.reset_notif_text()
        # Set the text above the central button
        self.notificationText2 = QLabel(self)
        self.notificationText2.move(15, 20)
        self.notificationText2.setText("Velkommen til Miljømærkning Danmarks stregkodescanner!"+ "\n" + "Tryk på nedestående knap og markér en stregkode for at scanne den" +"\n" +"Den scannede kode bliver automatisk indsat i din udklipsholder" + "\n"+"Tip: Prøv at zoome ind på stregkoden hvis den ikke scannes første gang")
        self.notificationText2.adjustSize()

        # Set the text below the central button
        self.notificationText3 = QLabel(self)
        self.notificationText3.move(15, 222)
        self.notificationText3.setText("For feedback og hjælp, kontakt tmo")
        self.notificationText3.adjustSize()

        
        
        
    # Function that changes the UI, when one starts snipping, and at the same time cleas the clipboard, so its ready for a new barcode to be inserted      
    def snip_search_clicked(self):
        
        self.snipWin = SnipWidget(self)
        self.snipWin.notification_signal.connect(self.reset_notif_text)
        self.snipWin.show()
        self.notificationText.setText("Klipper... Tryk ESC for at stoppe klipning")
        global dataSignal
        dataSignal = 0
        root = tk.Tk() 
        root.clipboard_clear() 
        root.clipboard_append("")
        self.update_notif()
        
      #Fucktion that changes the UI text, based on wether it has a scan on not.   
    def reset_notif_text(self):
        global dataSignal
        global dataRead
        global dataType
        global dataDirrection
        if dataSignal == 0:
            self.notificationText.setText("Venter på input...")
        else:
            self.notificationText.setText("Sucess stregkoden blev scannet og kopiret til udklipsholderen! "+"\n" +"Strekode id: " + dataRead +"\n"+"Stregkodetype: " + dataType +"\n"+"Stregkoderetning: "+ dataDirrection)
        self.update_notif()     
        

    def update_notif(self):
        self.notificationText.move(20, 155)
        self.notificationText.adjustSize()

        

        
        
# Funcktion that scans the snipped image for barcodes. 
def decode(image):
    global dataRead
    global dataType
    global dataDirrection
    dataRead = 0 
    image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY) 
    decoded_objects = pyzbar.decode(image) # This line analyses the barcodes
    for obj in decoded_objects:
        # draw the barcode
        image = draw_barcode(obj, image)
        dataRead = obj.data.decode() # The function above spits out a barcode, as the wrong data type, this gets it as an integer
        dataType = obj.type
        dataDirrection = obj.orientation 
        root = tk.Tk()
        root.clipboard_clear() #Cleas the clipboard, and inserts the new barcode value
        root.clipboard_append(dataRead)
        global dataSignal
        dataSignal = 1
        

        
    
    return image

#This draws the barcode with a green square around it, so the use know it got a hit
def draw_barcode(decoded, image):
    image = decoedImage
    image = cv2.rectangle(image, (decoded.rect.left, decoded.rect.top), 
                            (decoded.rect.left + decoded.rect.width, decoded.rect.top + decoded.rect.height),
                            color=(0, 255, 0),
                            thickness=5)                     
    return image       
        
    

#The class contaning the snipping tool
class SnipWidget(QMainWindow):
    
    notification_signal = pyqtSignal() # Sends a signal to the UI, when something has happend
    
    #Initates the snipping tool. 
    def __init__(self, ButtonPressed):
        super(SnipWidget, self).__init__() 
        self.ButtonPressed = ButtonPressed
        root = tk.Tk()# instantiates window
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setWindowTitle(' ')
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.setWindowOpacity(0.3)
        self.is_snipping = False #Variable som skifter mens man klipper
        QtWidgets.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.CrossCursor)
        )
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.c = Communicate()
        self.show()
        self.c.snip_saved.connect(self.DecodeAndShow)
        
      
            
        
            
    # Adds a green opaque window, that the uses cuts on, just like the windows snipping tool.      
    def paintEvent(self, event):
        if self.is_snipping:
            brush_color = (0, 0, 0, 0)
            lw = 0
            opacity = 0
        else:
            brush_color = (35, 155, 86, 128)
            lw = 3
            opacity = 0.3 

        self.setWindowOpacity(opacity)
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor('black'), lw))
        qp.setBrush(QtGui.QColor(*brush_color))
        qp.drawRect(QtCore.QRect(self.begin, self.end))

    #Function that cloes the opaque window when esc is pressed
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            print('Quit')
            QtWidgets.QApplication.restoreOverrideCursor();
            self.notification_signal.emit()
            self.close()
        event.accept()

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()


    # Main function, that evaluates what happens when the button is pressed. 
    def mouseReleaseEvent(self, event):
        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())
        self.is_snipping = True        
        self.repaint()
        QtWidgets.QApplication.processEvents()
        if x1 == x2 or y1 == y2: 
            QtWidgets.QApplication.restoreOverrideCursor();
            self.notification_signal.emit()
            self.close()
        else:
            img = ImageGrab.grab(bbox=(x1, y1, x2+1, y2+1))
            self.is_snipping = False
            self.repaint()
            QtWidgets.QApplication.processEvents()
            self.img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
            QtWidgets.QApplication.restoreOverrideCursor();
            self.c.snip_saved.emit()
            self.close()
    

    # Function that opens a small window displaying the barcode drawn above. 
    def DecodeAndShow(self):
        global decoedImage

        decoedImage = self.img
        decoedImage = decode(decoedImage)
        cv2.imshow("Udklip", decoedImage)
        if dataRead != 0:
            global dataSignal
            dataSignal = 1
            self.notification_signal.emit()
            
        



    
    
        
#Function that start the UI window. 
def window():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarktheme.load_stylesheet("light"))
    
    win = MyWindow()
    win.show()
    
    sys.exit(app.exec_())
    
window()