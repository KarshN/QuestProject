import time
from PIL import Image
import numpy as np
from numpy import asarray
import pytesseract
from pytesseract import Output
from translate import Translator
from gpiozero import Button
from unidecode import unidecode
from functools import partial
from gtts import gTTS
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import cv2
import sys

from PyQt5.QtWidgets import QApplication, QOpenGLWidget, QToolButton, QPushButton, QAction, QLabel, QMenu, QVBoxLayout, QHBoxLayout, QWidget
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal 
from picamera2.previews.qt import QGlPicamera2
from picamera2 import Picamera2, Preview
import libcamera
from libcamera import Transform
borderScale=2
picam2 = Picamera2()
picam2.set_controls({'HdrMode': libcamera.controls.HdrModeEnum.SingleExposure})
still_config=picam2.create_still_configuration()
vid_config=picam2.create_preview_configuration(transform=Transform(vflip=1,hflip=1))
picam2.configure(vid_config)
time.sleep(0.5)
#picam2.start(vid_config)

#picam2.start_preview(Preview.QTGL,width=800,height=600)
app = QApplication(sys.argv)

print(dir(QPushButton()))

from PyQt5.QtWidgets import QLayout, QWidgetItem

def textDimensions(text,font,font_scale,font_thickness):
    textSize, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    return textSize
def drawTextBg(img, text, pos, font, font_scale, text_color,font_thickness,text_color_bg):
    x, y = pos
    text_w, text_h = textDimensions(text,font,font_scale,font_thickness)
    cv2.rectangle(img, pos, (round(x + text_w), round(y + text_h)), text_color_bg, -1)
    cv2.putText(img, text, (x, round(y + text_h + font_scale - 1)), font, font_scale, text_color, font_thickness)
class SquidButton():
    def __init__(self,pin,cooldown,thread):
        self.button=Button(pin)
        self.alreadyPressed=False
        self.timer=QTimer()
        self.timer.timeout.connect(self.endCoolDown)
        self.timerLength=cooldown
        self.thread=thread
        self.button.when_pressed=self.button_pressed
    def button_pressed(self,event=None):
        if((self.alreadyPressed is False)):
            if(window.border is True):
                self.thread.capture_image()
                self.alreadyPressed=True
                self.timer.start(self.timerLength)
                scanButton.text="Clear Overlay"
            else:
                window.border=True
                self.alreadyPressed=True
                self.timer.start(self.timerLength-9)
                window.message="Bring text into view"
                window.overlayBorder(window.wWidth/borderScale,window.wHeight/borderScale)
                scanButton.text="Scan!"
            scanButton.updateText()
    def endCoolDown(self):
        self.alreadyPressed=False
class toggleButton():
    def __init__(self,text,id,squid,state="Off"):
        self.text=text
        self.state=state
        self.button=QPushButton()
        self.squid=squid
        self.id=id
        if(id=="audio" or id=="translate"):
            self.button.setText(self.text+": "+self.state)
            self.button.mousePressEvent=self.changeState
            if(id=="audio"):
                window.cameraThread.sound=(state=="On")
            else:
                window.cameraThread.translate=(state=="On")
                if(state=="Off"):
                    translateObj.changeLang("en","en")
                    to_Lang.selection=0
                    from_Lang.selection=0
        else:
            self.button.setText(self.text)
            self.button.mousePressEvent=self.squid.button_pressed
    def changeState(self,event):
        if(self.state=="Off"):
            self.state="On"
        else:
            self.state="Off"
        if(self.id=="audio"):
            window.cameraThread.sound=(self.state=="On")
        else:
            window.cameraThread.translate=(self.state=="On")
            if(self.state=="Off"):
                translateObj.changeLang("en","en")
                to_Lang.selection=0
                from_Lang.selection=0
                print(translateObj.langFrom,translateObj.langTo)
            window.redoLayout(from_Lang,to_Lang,scanButton,toggleAudio,toggleTranslate,(self.state=="On"))
        self.updateText(True)
    def updateText(self,state=False):
        if(state is False):
            self.button.setText(self.text)
        else:
            self.button.setText(self.text+": "+self.state)
            
class menu():
    def __init__(self,selection,id):
        self.id=id
        self.button=QToolButton()
        self.menu=QMenu(self.button)
        self.actions=[]
        if(self.id=="toLang"):
            self.options=["English", "Spanish", "Arabic", "Chinese", "Hindi", "French", "Bengali", "Portuguese", "Russian", "Japanese", "Punjabi", "German", "Javanese", "Korean", "Vietnamese", "Telugu", "Marathi", "Turkish", "Tamil", "Urdu", "Italian", "Polish", "Ukrainian", "Romanian", "Dutch", "Greek", "Czech", "Swedish", "Hungarian", "Arabic", "Thai", "Malay", "Swahili", "Hebrew", "Norwegian", "Finnish", "Danish", "Hungarian", "Vietnamese", "Tagalog"]
            self.abbrs=["en", "es", "ar", "zh", "hi", "fr", "bn", "pt", "ru", "ja", "pa", "de", "jv", "ko", "vi", "te", "mr", "tr", "ta", "ur", "it", "pl", "uk", "ro", "nl", "el", "cs", "sv", "hu", "th", "ms", "sw", "he", "no", "fi", "da"]

        else:
            #hebrew doesn't work for some reason
            self.options=["English", "Spanish", "Arabic", "French", "German", "Italian", "Russian", "Japanese", "Portuguese", "Dutch", "Polish", "Korean", "Chinese (Simplified)", "Chinese (Traditional)", "Turkish", "Hindi", "Bengali", "Serbian", "Ukrainian", "Swedish", "Croatian", "Czech", "Danish", "Finnish", "Norwegian", "Greek", "Bulgarian", "Slovak", "Latvian", "Indonesian", "Tamil", "Telugu", "Marathi", "Malay", "Basque", "Irish", "Slovenian"]
            self.abbrs=["en", "es", "ar", "fr", "de", "it", "ru", "ja", "pt", "nl", "pl", "ko", "zh", "zh", "tr", "hi", "bn", "sr", "uk", "sv", "hr", "cs", "da", "fi", "no", "el", "bg", "sk", "lv", "id", "ta", "te", "mr", "ms", "eu", "ga", "sl"]
            self.abbrs_3=["eng", "spa", "ara", "fra", "deu", "ita", "rus", "jpn", "por", "nld", "pol", "kor", "chi_sim", "chi_tra" "tur", "hin", "ben", "srp", "ukr", "swe", "hrv", "ces", "dan", "fin", "nor", "ell", "bul", "slk", "lat", "ind", "tam", "tel", "mar", "mal", "eus", "gle", "slv"]
            #for pyTesseract

        #these are common langs, expanded list below (102 langs)
        #self.options= ["Afrikaans", "Amharic", "Arabic", "Azerbaijani", "Belarusian", "Bulgarian", "Bengali", "Bosnian", "Catalan", "Cebuano", "Corsican", "Czech", "Welsh", "Danish", "German", "Greek", "English", "Esperanto", "Spanish", "Estonian", "Basque", "Persian", "Finnish", "French", "Frisian", "Irish", "Scottish Gaelic", "Galician", "Gujarati", "Haitian Creole", "Hebrew", "Hindi", "Croatian", "Haitian", "Hungarian", "Armenian", "Indonesian", "Igbo", "Icelandic", "Italian", "Japanese", "Javanese", "Georgian", "Kazakh", "Khmer", "Kannada",  "Korean", "Kurdish", "Kyrgyz", "Latin", "Luxembourgish", "Lao", "Lithuanian", "Latvian", "Malagasy", "Maori", "Macedonian", "Malayalam", "Mongolian", "Marathi", "Malay", "Maltese", "Myanmar", "Nepali", "Dutch", "Norwegian", "Chichewa", "Punjabi", "Polish", "Pashto", "Portuguese", "Romanian", "Russian", "Kinyarwanda", "Sindhi", "Sinhala", "Slovak", "Slovenian", "Samoan", "Shona", "Somali", "Albanian", "Serbian", "Sesotho", "Sundanese", "Swedish", "Swahili", "Tamil", "Telugu", "Tajik", "Thai", "Tagalog", "Turkish", "Uighur", "Ukrainian", "Urdu", "Uzbek", "Vietnamese", "Xhosa", "Yiddish", "Yoruba", "Chinese", "Zulu"]
        #self.abbrs=["af", "am", "ar", "az", "be", "bg", "bn", "bs", "ca", "ceb", "co", "cs", "cy", "da", "de","el", "en", "eo", "es", "et", "eu", "fa", "fi", "fr", "fy", "ga", "gd", "gl", "gu", "ha","he", "hi", "hr", "ht", "hu", "hy", "id", "ig", "is", "it", "ja", "jv", "ka", "kk", "km","kn", "ko", "ku", "ky", "la", "lb", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "no", "ny", "pa", "pl", "ps", "pt", "ro", "ru", "rw", "sd","si", "sk", "sl", "sm", "sn", "so", "sq", "sr", "st", "su", "sv", "sw", "ta", "te", "tg","th", "tl", "tr", "ug", "uk", "ur", "uz", "vi", "xh", "yi", "yo", "zh", "zu"]
        self.selection=selection
        self.partials=[]
        for i in range(0,len(self.options)):
            self.actions.append(QAction(self.options[i]))
            self.menu.addAction(self.actions[i])
            self.partials.append(partial(self.setTo,self.options[i],i))
            self.actions[i].triggered.connect(self.partials[i])
        self.button.setPopupMode(self.button.ToolButtonPopupMode.MenuButtonPopup)
        #self.button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
        self.button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonFollowStyle)
        self.button.setMenu(self.menu)
        self.button.setText(self.options[self.selection])
    def setTo(self,text,num):
        self.selection=num
        self.button.setText(text)
        if(self.id=="toLang"):
            translateObj.changeLang(translateObj.langFrom,self.abbrs[self.selection])
        else:
            translateObj.changeLang(self.abbrs[self.selection],translateObj.langFrom)
        print(num)
class textTranslator():
    def __init__(self,langFrom,langTo):
        self.langFrom=langFrom
        self.langTo=langTo
        self.translator=Translator(to_lang=langTo,from_lang=langFrom)
    def changeLang(self,langFrom,langTo):
        self.langFrom=langFrom
        self.langTo=langTo
        self.translator=Translator(to_lang=langTo,from_lang=langFrom)
        print(langTo,langFrom)
class CameraThread(QThread):

    def __init__(self, picam2, qpicam2, still_config,sound,translate):
        super().__init__()
        self.picam2 = picam2
        self.qpicam2= qpicam2
        self.qpicam2.done_signal.connect(self.processImg)
        self.stillConfig = still_config
        self.textRead=""
        self.translatedText=""
        self.originalTranslated=""
        self.bounds=[]
        self.sound=sound
        self.translate=translate
        #self.timer = QTimer(self)
        #self.timer.timeout.connect(self.capture_image)
        #self.timer.start(5000)
    def run(self):
        self.exec_()

    def capture_image(self):
        #self.stillConfig=self.picam2.create_still_configuration()
        translateObj.changeLang(from_Lang.abbrs[from_Lang.selection],to_Lang.abbrs[to_Lang.selection])
        window.message="Detecting text..."
        window.border=True
        window.overlayBorder(window.wWidth/borderScale,window.wHeight/borderScale)
        self.picam2.switch_mode_and_capture_array(self.stillConfig, "main", signal_function=self.qpicam2.signal_done)
    def processImg(self,job):
        img=picam2.wait(job)
        croppedImg=np.fliplr(np.flipud(img[round(img.shape[0]/2-img.shape[0]/6.4):round(img.shape[0]/2+img.shape[0]/6.4),round(img.shape[1]/2-img.shape[1]/6.4):round(img.shape[1]/2+img.shape[1]/6.4)]))
        self.textRead=pytesseract.image_to_string(croppedImg, lang=from_Lang.abbrs_3[from_Lang.selection])
        self.bounds=pytesseract.image_to_data(croppedImg,lang=from_Lang.abbrs_3[from_Lang.selection],output_type=Output.DICT)
        if(self.textRead=="" or self.textRead==" "):
            window.message="No text detected"
        else:
            window.message="Text detected!"
        print(f"shape: {croppedImg.shape}")
        self.processText()
        window.border=False
        window.overlayBorder(window.wWidth/borderScale,window.wHeight/borderScale)
        if(self.originalTranslated!="" and self.sound is True):
            self.processSound(self.originalTranslated)
        #imgObj=Image.fromarray(croppedImg)
        #imgObj.save("image-display.jpg")
    def processText(self):
        finText=''
        boxes=np.zeros((window.wHeight,window.wWidth,4), dtype=np.uint8)
        for i in range(0, len(self.bounds['level'])):
            if(self.bounds['text'][i]!=''):
                finText=finText+self.bounds['text'][i]+' '
        if(self.translate is True):
            translateFin=translateObj.translator.translate(finText)
        else:
            translateFin=finText
        if(finText=="" or finText==" " or translateFin==""):
            print("no detected")
            finText="No text detected. Make sure text is in focus and visible."
        if(finText!=''):
            boxes[round(window.wHeight/2-window.wHeight/4):round(window.wHeight/2+window.wHeight/4),round(window.wWidth/2-window.wWidth/4):round(window.wWidth/2+window.wWidth/4)]=(240,240,240,100)
        print(finText)
        print(f"image: {translateFin}")
        if(finText=="No text detected. Make sure text is in focus and visible."):
            fromEng=Translator(to_lang=translateObj.langTo)
            if(self.translate is True):
                self.originalTranslated=fromEng.translate(finText)
                self.translatedText=unidecode(self.originalTranslated)
            else:
                self.originalTranslated=finText
                self.translatedText=finText
        else:
            self.originalTranslated=translateFin
            self.translatedText=unidecode(translateFin)
        window.overlay=boxes
        words=self.translatedText.split(" ")
        print(words)
        textLines=['']
        for i in range(0,len(words)):
            if(textDimensions(textLines[-1],cv2.FONT_HERSHEY_DUPLEX,0.7,1)[0]<=window.wHeight/2-22):
                textLines[-1]=textLines[-1]+words[i]+" "
            else:
                textLines.append(words[i]+" ")
        print(textLines)
        for t in range(0,len(textLines)):
            pos=(round(window.wWidth/2-window.wWidth/(2*borderScale))+100,round(window.wHeight/2)+11+round((textDimensions(textLines[-1],cv2.FONT_HERSHEY_DUPLEX,0.7,1)[1]+5)*(t-len(textLines)/2))) 
            drawTextBg(boxes,textLines[t],pos,cv2.FONT_HERSHEY_DUPLEX,0.7,(0,0,0,255),1,(255,255,255,255))
    def processSound(self,text):
        textToSpeech = gTTS(text, lang=to_Lang.abbrs[to_Lang.selection])
        textToSpeech.save("speech.mp3")
        sound=AudioSegment.from_mp3("speech.mp3")
        play(sound)
    def scaleCoords(self,x,y):
        return (round((y+891)/4.5),round((x+1584)/4.5))


class QGlCameraWindow(QOpenGLWidget):
    def __init__(self,wWidth,wHeight,sound,translate):
        super().__init__()
        self.wWidth=wWidth
        self.wHeight=wHeight
        self.qpicamera2 = QGlPicamera2(picam2, width=wWidth, height=wHeight, keep_ar=False)
        #self.qpicamera2 = QGlPicamera2(picam2, width=1024, height=600, keep_ar=False)
        self.preview=QWidget()

        self.cameraThread = CameraThread(picam2, self.qpicamera2, still_config,sound,translate)
        self.cameraThread.start()

        #self.timer=QTimer(self)
        #self.timer.timeout.connect(self.updOverlay)
        #self.timer.start(1000)
        self.overlay=np.zeros((self.wHeight,self.wWidth,4), dtype=np.uint8)
        self.message="Bring text into view"
        self.border=True
        picam2.start()
    
    def setWindowLayout(self,menu,menu2,toggle1,toggle2,toggle3,translate=True):
        
        self.QVLayout=QVBoxLayout()
        self.QVLayout.addWidget(self.qpicamera2)

        #self.toggles=QHBoxLayout()
        #self.toggles.addWidget(toggle2.button)
        #self.toggles.addWidget(toggle3.button)
        #self.QVLayout.addLayout(self.toggles)

        self.bottomBar=QHBoxLayout()
        self.bottomBar.addWidget(toggle3.button)
        if(True):
            self.bottomBar.setAlignment(toggle3.button,Qt.AlignLeft)
            self.fromLabel=QLabel("Translating from:",menu.button)
            self.fromLabel.setHidden(not translate)
            self.bottomBar.addWidget(self.fromLabel)
            self.bottomBar.setAlignment(self.fromLabel,Qt.AlignRight)
            self.bottomBar.addWidget(menu.button)
            self.bottomBar.setAlignment(menu.button,Qt.AlignLeft)
            self.bottomBar.addWidget(toggle1.button)
            self.bottomBar.setAlignment(toggle1.button,Qt.AlignCenter)
            self.toLabel=QLabel("Translating to:",menu2.button)
            self.bottomBar.addWidget(self.toLabel)
            self.bottomBar.setAlignment(self.toLabel,Qt.AlignRight)
            self.bottomBar.addWidget(menu2.button)
            self.bottomBar.setAlignment(menu2.button,Qt.AlignLeft)
        self.bottomBar.addWidget(toggle2.button)
        self.bottomBar.setAlignment(toggle2.button,Qt.AlignRight)
        self.QVLayout.addLayout(self.bottomBar)

        self.preview.setWindowTitle("Text Translation App")
        self.preview.setStyleSheet("background-color: dimgray;")
        self.preview.resize(self.wWidth,self.wHeight+100)
        self.preview.setLayout(self.QVLayout)
    def redoLayout(self,menu,menu2,toggle1,toggle2,toggle3,translate):
        menu.button.setHidden(not translate)
        menu2.button.setHidden(not translate)
        if(translate):
            self.fromLabel.setText("Translating from:")
            self.toLabel.setText("Translating to:")
        else:
            self.fromLabel.setText(" ")
            self.toLabel.setText(" ")

    def overlayBorder(self,width,height):
        x=round(self.wWidth/2)
        y=round(self.wHeight/2)
        overlayNP = np.zeros((self.wHeight,self.wWidth, 4), dtype=np.uint8)
        if self.border is True:
            overlayNP[round(y-height/2)-1:round(y-height/2)+1,round(x-width/2):round(x+width/2)]=(247, 233, 37,255)
            overlayNP[round(y+height/2)-1:round(y+height/2)+1,round(x-width/2):round(x+width/2)]=(247, 233, 37,255)
            overlayNP[round(y-height/2):round(y+height/2),round(x-width/2)-1:round(x-width/2)+1]=(247, 233, 37,255)
            overlayNP[round(y-height/2):round(y+height/2),round(x+width/2)-1:round(x+width/2)+1]=(247, 233, 37,255)
        else:
            overlayNP=self.overlay
        #font is hershey duplex
        drawTextBg(overlayNP,self.message,(x+round(1.1*width/2),y-round(0.9*height/2)),cv2.FONT_HERSHEY_DUPLEX,0.7,(247, 233, 37,200),1,(255,255,255,10))
        self.qpicamera2.set_overlay(overlayNP)
    def overlayImg(self,src,x_off,y_off,imgW,imgH):
        x=round(self.wWidth/2+x_off-imgW/2)
        y=round(self.wHeight/2+y_off-imgH/2)
        overlayImg=Image.open(src).resize((imgW,imgH))
        overlayArr = np.asarray(overlayImg.convert("RGBA"))
        overlayNP = np.zeros((self.wHeight,self.wWidth, 4), dtype=np.uint8)
        overlayNP[y:y+imgH,x:x+imgW]=overlayArr
        #overlayNP[:150, 250:] = (255, 0, 0, 64)
        #overlayNP[150:, :200] = (0, 255, 0, 64)
        #overlayNP[150:, 300:] = (0, 0, 255, 64)
        self.qpicamera2.set_overlay(overlayNP)
    def show(self):
        self.qpicamera2.show()
    def updOverlay(self):
        pass

translateObj=textTranslator("en","es")
to_Lang=menu(1,"toLang")
from_Lang=menu(0,"fromLang")
window=QGlCameraWindow(1024,576,False,False)
button=SquidButton(25,10,window.cameraThread)
toggleAudio=toggleButton("Text to Speech Mode","audio",button,"Off")
toggleTranslate=toggleButton("Translation","translate",button,"On")
scanButton=toggleButton("Scan!","scan",button)
window.setWindowLayout(from_Lang,to_Lang,scanButton,toggleAudio,toggleTranslate)
#app.processEvents()
#window.overlayImg("OCRTest.png",0,0,200,150)
window.border=True
window.overlayBorder(window.wWidth/borderScale,window.wHeight/borderScale)
#print(window.wWidth,window.wHeight)
window.preview.show()
app.exec()
