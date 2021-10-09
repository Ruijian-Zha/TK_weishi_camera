import sys
import os
import shutil
from MVGigE import *
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox, QLabel, QFileDialog, QScrollArea, QComboBox, QLineEdit, QSlider, QGridLayout, QGroupBox, QCheckBox
from PyQt5.QtGui import QPixmap, QPalette, QImage, QIcon
from PyQt5.QtCore import Qt

import time


class MVCam(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        # test auto
        self.openCam()
        self.startGrab()
        # self.btnSave.clicked.emit(0)
        self.saveImage()
        # self.closeCam()
        # return 0

    def initUI(self):
        # 以下是使用pyqt5初始化UI界面
        self.setGeometry(100, 100, 700, 650)
        self.setWindowTitle('SingGrab')
        self.setWindowIcon(QIcon('GCap.ico'))
        self.btnOpen = QPushButton('打开相机', self)
        self.combo = QComboBox(self)
        self.combo.addItem('25%')
        self.combo.addItem('50%')
        self.combo.addItem('100%')
        self.combo.setCurrentIndex(2)
        self.btnStart = QPushButton('开始采集', self)
        self.btnPause = QPushButton('暂停采集', self)
        self.btnSave = QPushButton('保存图像', self)
        self.btnSetting = QPushButton('设置', self)
        self.btnClose = QPushButton('关闭相机', self)
        self.combo.setEnabled(False)
        self.btnStart.setEnabled(False)
        self.btnPause.setEnabled(False)
        self.btnSave.setEnabled(False)
        self.btnSetting.setEnabled(False)
        self.btnClose.setEnabled(False)

        self.label = QLabel(self)
        self.QScrollArea = QScrollArea(self)
        self.QScrollArea.setBackgroundRole(QPalette.Dark)
        self.QScrollArea.setWidget(self.label)

        self.winid = self.label.winId()  # 获取label对象的句柄
        self.label.setStyleSheet("QLabel{background:Dark;}")
        hbox = QHBoxLayout()
        hbox.addWidget(self.btnOpen)
        hbox.addWidget(self.combo)
        hbox.addWidget(self.btnStart)
        hbox.addWidget(self.btnPause)
        hbox.addWidget(self.btnSave)
        hbox.addWidget(self.btnSetting)
        hbox.addWidget(self.btnClose)

        hbox.addStretch(1)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.QScrollArea)
        self.setLayout(vbox)

        # 使用的信号槽机制连接触发事件
        self.btnOpen.clicked.connect(self.openCam)
        self.combo.activated[str].connect(self.setSize)
        self.btnStart.clicked.connect(self.startGrab)
        self.btnPause.clicked.connect(self.pauseGrab)
        self.btnSave.clicked.connect(self.saveImage)
        self.btnSetting.clicked.connect(self.setting)
        self.btnClose.clicked.connect(self.closeCam)
        self.show()

    def setting(self):
        self.setui = settingUI(self.hCam)
        self.setui.show()

    # 点击界面打开相机按钮，执行本函数
    def openCam(self):
        r = MVInitLib()  # 初始化函数库
        if (r != MVSTATUS_CODES.MVST_SUCCESS):
            msgBox = QMessageBox(QMessageBox.Warning, '提示', '函数库初始化失败！')
            msgBox.exec()
            return
        r = MVUpdateCameraList()  # 查找连接到计算机上的相机
        if (r != MVSTATUS_CODES.MVST_SUCCESS):
            msgBox = QMessageBox(QMessageBox.Warning, '提示', '查找连接计算机失败！')
            msgBox.exec()
            return
        nCams = MVGetNumOfCameras()  # 获取相机数量
        if(nCams.status != MVSTATUS_CODES.MVST_SUCCESS):
            msgBox = QMessageBox(QMessageBox.Warning, '提示', nCams.status)
            msgBox.exec()
            return
        if(nCams.num == 0):
            msgBox = QMessageBox(QMessageBox.Warning, '提示', '没有找到相机,请确认连接和相机IP设置!')
            msgBox.exec()
            return
        hCam = MVOpenCamByIndex(0)  # 根据相机的索引返回相机句柄
        if(hCam.hCam == 0):
            if(hCam.status == MVSTATUS_CODES.MVST_ACCESS_DENIED):
                msgBox = QMessageBox(QMessageBox.Warning,'提示', '无法打开相机，可能正被别的软件控制!')
                msgBox.exec()
                return
            else:
                msgBox = QMessageBox(QMessageBox.Warning, '提示', '无法打开相机!')
                msgBox.exec()
                return
        w = MVGetWidth(hCam.hCam)  # 获取图像宽度
        h = MVGetHeight(hCam.hCam)  # 获取图像高度
        pf = MVGetPixelFormat(hCam.hCam)  # 获取图像格式
        self.hCam = hCam.hCam
        self.width = w.width
        self.height = h.height
        self.pixelFormat = pf.pixelFormat
        if(self.pixelFormat == MV_PixelFormatEnums.PixelFormat_Mono8):
            self.himage = MVImageCreate(self.width, self.height, 8).himage  # 创建图像句柄
        else:
            self.himage = MVImageCreate(self.width, self.height, 24).himage  # 创建图像句柄
        self.label.resize(self.width, self.height)
        self.btnOpen.setEnabled(False)
        self.combo.setEnabled(True)
        self.btnStart.setEnabled(True)
        self.btnPause.setEnabled(False)
        self.btnSave.setEnabled(False)
        self.btnSetting.setEnabled(True)
        self.btnClose.setEnabled(True)

    # 本函数是修改显示比例
    def setSize(self, text):
        if(text == '25%'):
            width = int(self.width*0.25)
            height = int(self.height*0.25)
            self.label.resize(width, height)
            MVSetGrabWindow(self.hCam, width, height)  # 设置采集图像的比例
        elif(text == '50%'):
            width = int(self.width*0.5)
            height = int(self.height*0.5)
            self.label.resize(width, height)
            MVSetGrabWindow(self.hCam, width, height)
        else:
            width = self.width
            height = self.height
            self.label.resize(width, height)
            MVSetGrabWindow(self.hCam, width, height)

    def startGrab(self):  # 开始采集执行本函数
        mode = MVGetTriggerMode(self.hCam)  # 获取当前相机采集模式
        source = MVGetTriggerSource(self.hCam)  # 获取当前相机信号源

        # ****************
        #if(self.sender().text() == '开始采集'):
        if(True):
            if(mode.pMode == TriggerModeEnums.TriggerMode_Off):  # 当触发模式关闭的时候，界面的行为
                self.btnStart.setText('停止采集')
                MVStartGrabWindow(self.hCam, self.winid)  # 将采集的图像传输到指定窗口
                self.btnOpen.setEnabled(False)
                self.combo.setEnabled(True)
                self.btnStart.setEnabled(True)
                self.btnPause.setEnabled(True)
                self.btnSave.setEnabled(True)
                self.btnSetting.setEnabled(False)
                self.btnClose.setEnabled(True)
            else:
                if( source.source == TriggerSourceEnums.TriggerSource_Software):  # 当触发模式打开且为软触发的时候，界面的行为
                    MVStartGrabWindow(self.hCam, self.winid)  # 将采集的图像传输到指定窗口
                    MVTriggerSoftware(self.hCam)
                    self.btnOpen.setEnabled(False)
                    self.combo.setEnabled(True)
                    self.btnStart.setEnabled(True)
                    self.btnPause.setEnabled(False)
                    self.btnSave.setEnabled(True)
                    self.btnSetting.setEnabled(True)
                    self.btnClose.setEnabled(True)
                else:  # 当触发模式打开且为外触发的时候，界面的行为
                    MVStartGrabWindow(self.hCam, self.winid)  # 将采集的图像传输到指定窗口
                    self.btnOpen.setEnabled(False)
                    self.combo.setEnabled(True)
                    self.btnStart.setEnabled(True)
                    self.btnPause.setEnabled(False)
                    self.btnSave.setEnabled(True)
                    self.btnSetting.setEnabled(True)
                    self.btnClose.setEnabled(True)
        else:
            self.btnStart.setText('开始采集')
            MVStopGrabWindow(self.hCam)  # 停止采集
            self.btnOpen.setEnabled(False)
            self.combo.setEnabled(True)
            self.btnStart.setEnabled(True)
            self.btnPause.setEnabled(False)
            self.btnSave.setEnabled(True)
            self.btnSetting.setEnabled(True)
            self.btnClose.setEnabled(True)

    def pauseGrab(self):  # 暂停或者继续执行本函数
        if(self.sender().text() == '继续采集'):
            self.btnPause.setText('暂停采集')
            MVFreezeGrabWindow(self.hCam, False)  # 恢复图像传输到指定窗口
            self.btnOpen.setEnabled(False)
            self.combo.setEnabled(True)
            self.btnStart.setEnabled(True)
            self.btnPause.setEnabled(True)
            self.btnSave.setEnabled(False)
            self.btnSetting.setEnabled(False)
            self.btnClose.setEnabled(True)
        else:
            self.btnPause.setText('继续采集')
            MVFreezeGrabWindow(self.hCam, True)  # 暂停将图像传输到指定窗口
            self.btnOpen.setEnabled(False)
            self.combo.setEnabled(True)
            self.btnStart.setEnabled(True)
            self.btnPause.setEnabled(True)
            self.btnSave.setEnabled(True)
            self.btnSetting.setEnabled(False)
            self.btnClose.setEnabled(True)

    def saveImage(self):  # 保存图片执行本函数，在非触发模式时，只有采集暂停是才可以保存
        idn = MVGetSampleGrab(self.hCam, self.himage)
        time.sleep(1)
        print(idn.idn)
        
        # fname, ok = QFileDialog.getSaveFileName(self, '打开文件', './Images' + str(idn.idn) + '.bmp', ("Images (*.bmp *.jpg *.tif *.raw)"))

        # print(fname)

        # # *** force input
        fname = 'D:/【code】/camera_distance/camera_distance/Images100.bmp'
        ok = True


        if ok:
            try:
              filename = os.path.basename(fname)  # 获取到需要存储的文件名
              pathname = os.path.join(os.getcwd(), filename)  # 获取带有文件名的文件路径
              
              newfile = '\\'.join(fname.split('/')[:-1])  # 需要存储到的新文件夹
              print(pathname)
              MVImageSave(self.himage, filename.encode('utf-8'))  # 将图片保存下来
              if (newfile != os.getcwd()):  # 将图片移动到指定文件夹下
                  try:
                      shutil.move(pathname, newfile)
                  except:
                      os.unlink(os.path.join(newfile, filename))
                      shutil.move(pathname, newfile)
              image = QImage(newfile + '\\' + filename)
              self.label.setPixmap(QPixmap.fromImage(image))  # 加载图片
            except:
               return 0
        else:
            return 0

        # app.exit(app.exec_())
        quit()
        # mode = MVGetTriggerMode(self.hCam)  # 获取当前相机采集模式
        # if(mode.pMode == TriggerModeEnums.TriggerMode_Off):
        #     self.btnOpen.setEnabled(False)
        #     self.combo.setEnabled(True)
        #     self.btnStart.setEnabled(True)
        #     self.btnPause.setEnabled(True)
        #     self.btnSave.setEnabled(True)
        #     self.btnSetting.setEnabled(False)
        #     self.btnClose.setEnabled(True)
        # else:
        #     self.btnOpen.setEnabled(False)
        #     self.combo.setEnabled(True)
        #     self.btnStart.setEnabled(True)
        #     self.btnPause.setEnabled(False)
        #     self.btnSave.setEnabled(True)
        #     self.btnSetting.setEnabled(True)
        #     self.btnClose.setEnabled(True)

    def closeCam(self):  # 关闭相机执行本函数
        result = MVCloseCam(self.hCam)
        self.combo.setCurrentIndex(2)
        self.btnStart.setText('开始采集')
        self.btnPause.setText('暂停采集')
        if (result.status != MVSTATUS_CODES.MVST_SUCCESS):
            msgBox = QMessageBox(QMessageBox.Warning, '提示', result.status)
            msgBox.exec()
        self.btnOpen.setEnabled(True)
        self.combo.setEnabled(False)
        self.btnStart.setEnabled(False)
        self.btnPause.setEnabled(False)
        self.btnSave.setEnabled(False)
        self.btnSetting.setEnabled(False)
        self.btnClose.setEnabled(False)


class settingUI(QWidget):
    """
    本类是在主窗口点击设置按钮弹出的设置子窗口，接受主窗口的相机句柄，以完成本窗口的设置功能。
    本例程列出的设置为包大小，包延迟，触发模式
    """

    def __init__(self, hCam):
        super().__init__()
        self.hCam = hCam
        self.initUI()

    def initUI(self):
        # 以下是pyqt5初始化设置窗口
        self.move(300, 200)
        self.setFixedSize(350, 450)
        self.setWindowTitle('设置')
        self.setWindowIcon(QIcon('GCap.ico'))
        self.dial1 = QSlider(Qt.Horizontal, self)
        self.edit1 = QLineEdit(self)
        self.edit1.setEnabled(False)
        self.edit1.setMaximumWidth(50)
        self.lmin1 = QLabel('1316', self)
        self.lmax1 = QLabel('8996', self)
        self.dial2 = QSlider(Qt.Horizontal, self)
        self.edit2 = QLineEdit(self)
        self.edit2.setEnabled(False)
        self.edit2.setMaximumWidth(50)
        self.lmin2 = QLabel('0', self)
        self.lmax2 = QLabel('65536', self)
        self.check = QCheckBox(self)
        self.labelOn = QLabel('打开触发模式', self)
        self.labelMode = QLabel('触发源', self)
        self.comboMode = QComboBox(self)
        self.comboMode.addItem('软触发')
        self.comboMode.addItem('外触发')
        self.labelDi = QLabel('触发沿', self)
        self.comboAct = QComboBox(self)
        self.comboAct.addItem('上升沿')
        self.comboAct.addItem('下降沿')
        groupBox1 = QGroupBox('包大小')
        gbox1 = QGridLayout()
        gbox1.addWidget(self.dial1, 0, 0, 1, 9)
        gbox1.addWidget(self.edit1, 0, 10)
        gbox1.addWidget(self.lmin1, 1, 0)
        gbox1.addWidget(self.lmax1, 1, 8)
        groupBox1.setLayout(gbox1)
        groupBox2 = QGroupBox('包延迟')
        gbox2 = QGridLayout()
        gbox2.addWidget(self.dial2, 0, 0, 1, 9)
        gbox2.addWidget(self.edit2, 0, 10)
        gbox2.addWidget(self.lmin2, 1, 0)
        gbox2.addWidget(self.lmax2, 1, 8)
        groupBox2.setLayout(gbox2)
        groupBox3 = QGroupBox('触发')
        gbox3 = QGridLayout()
        gbox3.setSpacing(35)
        gbox3.addWidget(self.check, 0, 0)
        gbox3.addWidget(self.labelOn, 0, 1)
        gbox3.addWidget(self.labelMode, 1, 0)
        gbox3.addWidget(self.comboMode, 1, 1)
        gbox3.addWidget(self.labelDi, 3, 0)
        gbox3.addWidget(self.comboAct, 3, 1)
        gbox3.setColumnStretch(0, 1)
        gbox3.setColumnStretch(1, 11)
        groupBox3.setLayout(gbox3)
        vlayout = QVBoxLayout()
        vlayout.addWidget(groupBox1)
        vlayout.addWidget(groupBox2)
        vlayout.addWidget(groupBox3)
        vlayout.addStretch()
        self.setLayout(vlayout)
        # 获取获取当前相机数据，来初始化窗口界面
        self.packetSize = MVGetPacketSize(self.hCam)    # 获取当前相机包大小
        self.packetDelay = MVGetPacketDelay(self.hCam)  # 获取当前相机包延迟
        self.mode = MVGetTriggerMode(self.hCam)  # 获取当前相机采集模式
        self.source = MVGetTriggerSource(self.hCam)  # 获取当前相机信号源
        self.active = MVGetTriggerActivation(self.hCam)  # 当采集模式为外采集时，获取信号的上升沿或者下降沿
        self.edit1.setText(str(self.packetSize.psize))
        self.edit2.setText(str(self.packetDelay.time_us))
        value1 = (self.packetSize.psize-1316)/(8996-1316)*99
        self.dial1.setValue(value1)
        value2 = self.packetDelay.time_us/65536*99
        self.dial2.setValue(value2)
        if(self.source.source == TriggerSourceEnums.TriggerSource_Software):  # 将当前信号源类型显示在界面上
            self.comboMode.setCurrentIndex(0)
        else:
            self.comboMode.setCurrentIndex(1)
        if(self.active.act == TriggerActivationEnums.TriggerActivation_RisingEdge):  # 将当前外采集模式信号模式显示在界面上
            self.comboAct.setCurrentIndex(0)
        else:
            self.comboAct.setCurrentIndex(1)
        if(self.mode.pMode == TriggerModeEnums.TriggerMode_Off):  # 将当前采集模式开关状态显示在界面上
            self.check.setCheckState(Qt.Unchecked)
            self.comboMode.setEnabled(False)
            self.comboAct.setEnabled(False)
        else:
            self.check.setCheckState(Qt.Checked)
            self.comboMode.setEnabled(True)
            if(self.source.source == TriggerSourceEnums.TriggerSource_Software):  # 只有当选择外触发模式时，才可选择触发沿
                self.comboAct.setEnabled(False)
            else:
                self.comboAct.setEnabled(True)
        # 以下是到部件的触发事件
        self.dial1.valueChanged.connect(self.changeEdit1)
        self.dial2.valueChanged.connect(self.changeEdit2)
        self.check.clicked.connect(self.changeStatus)
        self.comboMode.activated[str].connect(self.changeMode)
        self.comboAct.activated[str].connect(self.changeAct)

    def changeEdit1(self, value):  # 拉包大小QSlider滑块是修改相机包大小参数
        # 将QSlider滑块的区间设置到1316~8996区间
        newvalue = int((value/99)*(8996-1316)+1316)
        MVSetPacketSize(self.hCam, newvalue)
        self.edit1.setText(str(newvalue))

    def changeEdit2(self, value):  # 拉包大小QSlider滑块是修改相机包延迟参数
        newvalue = int((value/99)*65536)  # 将QSlider滑块的区间设置到0~65536区间
        MVSetPacketDelay(self.hCam, newvalue)
        self.edit2.setText(str(newvalue))

    def changeStatus(self, boo):  # 选择或不选择打开触发模式复选框是的操作
        if(boo):  # 打开触发模式时
            MVSetTriggerMode(self.hCam, TriggerModeEnums.TriggerMode_On)
            self.comboMode.setEnabled(True)
            if(self.source.source == TriggerSourceEnums.TriggerSource_Software):  # 只有当选择外触发模式时，才可选择触发沿
                self.comboAct.setEnabled(False)
            else:
                self.comboAct.setEnabled(True)
        else:  # 未选择打开触发模式时
            MVStopGrabWindow(self.hCam)
            MVSetTriggerMode(self.hCam, TriggerModeEnums.TriggerMode_Off)
            self.comboMode.setEnabled(False)
            if(self.source.source == TriggerSourceEnums.TriggerSource_Software):  # 只有当选择外触发模式时，才可选择触发沿
                self.comboAct.setEnabled(False)
            else:
                self.comboAct.setEnabled(True)

    def changeMode(self, text):  # 选择触发源时的触发事件
        if(text == '软触发'):  # 当选择软触发时执行
            MVSetTriggerSource(self.hCam, 0)
            self.comboAct.setEnabled(False)
        else:  # 选择外触发时执行
            MVSetTriggerSource(self.hCam, 2)
            self.comboAct.setEnabled(True)

    def changeAct(self, text):  # 当选择外触发时，选择触发极性，分别为上升沿和下降沿
        if(text == '上升沿'):
            MVSetTriggerActivation(self.hCam, 0)
        else:
            MVSetTriggerActivation(self.hCam, 1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    Cam = MVCam()
    app.exit(app.exec_())
