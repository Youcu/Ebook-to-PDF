import os
import sys
import time
import mss
import mss.tools
import pyautogui
import natsort
import shutil

from pynput import mouse
from pynput.keyboard import Key, Controller
from PIL import Image

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QMainWindow, QVBoxLayout, QHBoxLayout, QSlider, QProgressBar, QMessageBox

class MainWindow(QMainWindow):
    def __init__(self) -> None : 
        super().__init__()

        # Init Values
        self.num = 1
        self.posX1 = 0
        self.posY1 = 0
        self.posX2 = 0
        self.posY2 = 0
        self.total_page = 1
        self.speed = 0.1
        self.region = {}
        self.file_list = []

        # Application Title
        self.setWindowTitle("Transformate Ebook To PDF")

        # Button 
        self.buttonLU = QPushButton("Click Position")
        self.buttonRD = QPushButton("Click Position")
        self.buttonCreate = QPushButton("Create PDF")
        self.buttonCreate.setFixedSize(QSize(470, 50))
        self.buttonInit = QPushButton("Initialization")

        # Button Click Event
        self.buttonLU.clicked.connect(self.click_posLU) # Left UP
        self.buttonRD.clicked.connect(self.click_posRD) # Right Down
        self.buttonCreate.clicked.connect(self.click_btn) # Button Click
        self.buttonInit.clicked.connect(self.initialization) # init

        # Speed  Slider
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_label = QLabel(f'Catpure Speed : {self.speed :.1f}sec')
        font_speed = self.speed_label.font()

        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(20)
        self.speed_slider.setValue(1)
        self.speed_slider.valueChanged.connect(self.change_speed)

        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        font_speed.setPointSize(10)
        self.speed_label.setFont(font_speed)

        # Title
        self.title = QLabel('Transform E-Book To PDF', self)
        font_title = self.title.font()

        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter) # Title -> allign at Center
        font_title.setPointSize(20) # Title font size
        self.title.setFont(font_title) # Apply Font Setting to Title

        # Status
        self.stat = QLabel('', self)
        font_stat = self.stat.font()

        self.stat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_stat.setPointSize(18)
        font_stat.setBold(True)
        self.stat.setFont(font_stat)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Progress Bar Label
        self.progress_label = QLabel('0%', self)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_progress = self.progress_label.font()
        font_progress.setPointSize(10)
        self.progress_label.setFont(font_progress)

        # Sign
        self.sign = QLabel('Made By EastShine, Modified By Hooby', self)
        #self.sign = QLabel('Hooby', self)
        font_sign = self.stat.font()

        self.sign.setAlignment(Qt.AlignmentFlag.AlignRight)
        font_sign.setPointSize(10)
        font_sign.setItalic(True)
        self.sign.setFont(font_sign)

        # Labeling
        self.label_LU = QLabel('Image Top Left Corner Position (x,y)\t\t', self)
        self.label_LU_pos = QLabel('(0, 0)', self)
        self.label_RD = QLabel('Image Down Right Corner Position (x,y)\t', self)
        self.label_RD_pos = QLabel('(0, 0)', self)
        self.label_tot_page = QLabel('Total Pages\t\t')
        self.label_PDF_name = QLabel('PDF Name\t\t')

        # Prompt
        self.prompt_tot_page = QLineEdit() # Editable Line, prompt
        self.prompt_PDF_name = QLineEdit() # Editable Line

        self.prompt_tot_page.setPlaceholderText(" Input Total Pages. (If format 1/n -> (n-1))")
        self.prompt_PDF_name.setPlaceholderText(" Input PDF Name.")

        # Input Box
        boxLU = QHBoxLayout() # LU Prompt and Btn
        boxLU.addWidget(self.label_LU)
        boxLU.addWidget(self.label_LU_pos)
        boxLU.addWidget(self.buttonLU)

        boxRD = QHBoxLayout() # RD Prompt and Btn
        boxRD.addWidget(self.label_RD)
        boxRD.addWidget(self.label_RD_pos)
        boxRD.addWidget(self.buttonRD)

        box_tot_page = QHBoxLayout() # Total Pages Prompt and Input Box
        box_tot_page.addWidget(self.label_tot_page)
        box_tot_page.addWidget(self.prompt_tot_page)

        box_PDF_name = QHBoxLayout() # PDF Name Prompt and Input Box
        box_PDF_name.addWidget(self.label_PDF_name)
        box_PDF_name.addWidget(self.prompt_PDF_name)

        # Speed Slider Box
        box_slider = QHBoxLayout()
        box_slider.addWidget(self.speed_label) 
        box_slider.addWidget(self.speed_slider)

        # Initialization Box 
        box_init = QHBoxLayout()
        box_init.addWidget(self.buttonInit)
        box_init.addWidget(self.sign) # Made by EastShine, Modified by Hooby

        # Progress Bar Box
        box_progress = QHBoxLayout()
        box_progress.addWidget(self.progress_bar)
        box_progress.addWidget(self.progress_label)

        # Status Box
        box_stat = QHBoxLayout()
        box_stat.addWidget(self.stat)

        # Set Layout
        layout = QVBoxLayout()
        layout.addWidget(self.title) # Title

        layout.addStretch(1)
        layout.addLayout(boxLU) # LU
        layout.addStretch(1)
        layout.addLayout(boxRD) # RD
        layout.addStretch(1)
        layout.addLayout(box_tot_page) # Total Page
        layout.addStretch(1)
        layout.addLayout(box_PDF_name) # PDF Name
        layout.addStretch(4)
        layout.addLayout(box_slider) # Slider
        layout.addLayout(box_init) # Initialization
        layout.addLayout(box_progress) # Progress Bar
        layout.addLayout(box_stat) # Stat

        layout.addWidget(self.buttonCreate, alignment=Qt.AlignCenter) # Create PDF

        # Create Container for Layout
        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        # Control Window Size -> Fix
        self.setFixedSize(QSize(500, 450))

    def initialization(self):
        self.num = 1
        self.posX1 = 0
        self.posY1 = 0
        self.posX2 = 0
        self.posY2 = 0
        self.speed = 0.1
        self.total_page = 1
        self.region = {}
        self.label_LU_pos.setText('(0, 0)')
        self.label_RD_pos.setText('(0, 0)')
        self.prompt_tot_page.clear()
        self.prompt_PDF_name.clear()
        self.stat.clear()
        self.speed_slider.setValue(1)
        self.progress_bar.setValue(0)
        self.progress_label.setText('0%')

    def click_posLU(self):
        def on_click(x, y, button, pressed):
            self.posX1 = int(x)
            self.posY1 = int(y)
            self.label_LU_pos.setText(str(f'({int(x)}, {int(y)})'))
            print('Button : %s, Position : (%s, %s), Pressed : %s ' % (button, x, y, pressed))
            if not pressed:
                return False

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

    def click_posRD(self):
        def on_click(x, y, button, pressed):
            self.posX2 = int(x)
            self.posY2 = int(y)
            self.label_RD_pos.setText(str(f'({int(x)}, {int(y)})'))
            print('Button : %s, Position : (%s, %s), Pressed : %s ' % (button, x, y, pressed))
            if not pressed:
                return False

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
    
    def change_speed(self):
        self.speed = self.speed_slider.value() / 10.0
        self.speed_label.setText(f'Capture Speed : {self.speed : .1f}sec')

    def click_btn(self):
        if self.prompt_tot_page.text() == '':
            self.stat.setText('Input Pages')
            self.prompt_tot_page.setFocus()
            return

        if self.prompt_PDF_name.text() == '':
            self.stat.setText('Input PDF Name')
            self.prompt_PDF_name.setFocus()
            return

        pos_x, pos_y = pyautogui.position() # Return : Current Mouse Pos

        if not(os.path.isdir('pdf_images')):
            os.mkdir(os.path.join('pdf_images'))

        self.total_page = int(self.prompt_tot_page.text())

        # Capture a Part of Screen
        self.region = {'top': self.posY1, 'left': self.posX1, 'width': self.posX2 - self.posX1, 
                    'height': self.posY2 - self.posY1}

        m = mouse.Controller()
        mouse_left = mouse.Button.left
        kb_control = Controller() # Key Board Contorl

        self.stat.setText('PDF is being formatted...')
        QApplication.processEvents()  # Update UI
        
        print('BeforeActivate Ebook Program', self.posX1, self.posY1)
    
        try:
            # Click for Transition of Screen for Activatign Ebook-Program
            time.sleep(2)
            m.position = (self.posX1, self.posY1)

            time.sleep(2)
            m.click(mouse_left)
            print('Activate Ebook Program', self.posX1, self.posY1, m.position)
            time.sleep(2)
            m.position = (pos_x, pos_y)

            # Save File
            while self.num <= self.total_page:
                time.sleep(self.speed)

                # Capture
                with mss.mss() as sct:
                    # Grab the data
                    img = sct.grab(self.region)
                    # Save to the Picture File
                    mss.tools.to_png(img.rgb, img.size, output=f'pdf_images/img_{str(self.num).zfill(4)}.png')

                # Update progress bar
                progress = int((self.num / self.total_page) * 100)
                self.progress_bar.setValue(progress)
                self.progress_label.setText(f'{progress}%')
                QApplication.processEvents()  # Update UI

                # Next Page
                kb_control.press(Key.right)
                kb_control.release(Key.right)

                self.num += 1

            print("Complete Capture!")
            self.stat.setText('PDF is being formatted...')
            QApplication.processEvents()  # Update UI
            path = 'pdf_images'

            # Image File list
            self.file_list = os.listdir(path)
            self.file_list = natsort.natsorted(self.file_list)

            # Delete .DS_Store Filename 
            if '.DS_Store' in self.file_list:
                del self.file_list[0]

            img_list = []

            # Create a First Page of PDF
            img_path = 'pdf_images/' + self.file_list[0]
            im_buf = Image.open(img_path)
            cvt_rgb_0 = im_buf.convert('RGB')

            for i in self.file_list:
                img_path = 'pdf_images/' + i
                im_buf = Image.open(img_path)
                cvt_rgb = im_buf.convert('RGB')
                img_list.append(cvt_rgb)

            del img_list[0]

            pdf_name = self.prompt_PDF_name.text()
            if pdf_name == '':
                pdf_name = 'default'

            # 사용자 홈 디렉토리 기준 경로 설정
            home_dir = os.path.expanduser("~")  # '~'를 사용자 홈 디렉토리로 확장
            save_path = os.path.join(home_dir, "UniversityBooks")  # '~/UniversityBooks' 경로 생성

            # 폴더가 없으면 생성
            os.makedirs(save_path, exist_ok=True)

            # PDF 파일 이름 및 경로 설정
            pdf_name = os.path.join(save_path, pdf_name+'.pdf')

            cvt_rgb_0.save(pdf_name, save_all=True, append_images=img_list, quality=100)
            print("Complete PDF Transformation!")
            self.stat.setText('Complete PDF Transformation!')
            shutil.rmtree('pdf_images/')
            
            # Using QMessageBox instead of pyautogui.alert
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Complete Program! \nCheck “OK“ button to exit program")
            msg.setWindowTitle("Information")
            msg.setStandardButtons(QMessageBox.Ok)
            
            result = msg.exec()

            if result == QMessageBox.Ok:
                QApplication.quit()

        except Exception as e:
            print('Exception Occured. ', e)
            self.stat.setText('Error!. You should Exit the program and retry!')

        finally:
            self.num = 1
            self.file_list = []
            self.progress_bar.setValue(100)
            self.progress_label.setText('100%')
            QApplication.processEvents()  # Update UI

app = QApplication(sys.argv)

window = MainWindow()
window.show()

# Start Event Loop 
app.exec()

"""
! Notice 

저작권법 제 30조에 의거하여, 개인소장을 위한 경우의 복제는 허용.
단, 이를 공유하는 경우에는 위법 행위임
"""
