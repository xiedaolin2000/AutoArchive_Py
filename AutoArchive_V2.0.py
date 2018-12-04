# -*- coding: utf-8 -*-
# -*- coding: gb2312 -*-
#==========================================================================
#			SMAP自动归档Python脚本
#描述:
#	该功能实现了,把文件从指定的VSS上取文件下来,打开PB工具编译,编译完成后
#	对指定的文件按照要求进行压缩,把压缩后的文件上传到Unix服务器上进行打包,生成一个升级包
#	把生成后的升级包取下来.
#
#作者:	谢道林
#日期:	2008-09-28
#版本：V2.0
#历史:
#
#
#
#
#
#
#
#	********************************************************************
# Bug list
#  * 在服务器上打完BIN包以后，删除原zip文件
#	* 如果目标目录存在文件，使用个体函数不能取最新的文件。
#==========================================================================
import getpass
import sys
import os
import socket
import telnetlib	#为了使用Telnet功能
import ftplib		#启用FTP功能
import zipfile 		#启用压缩功能
import distutils.file_util	#使用一些文件操作函数功能
import win32com.client  #导入win32com库 SourceSafe.0
import _winreg
from PyQt4 import QtCore, QtGui, uic


#显示一些详细信息
def prn(Text,Flag=0):
	print(Text)
	return

#操作Windows注册表的一个类
class CWinReg():
    '''封装了对Windows注册表进行操作
    参见 OpenKey() (in module _winreg)'''
    def __init__(self, RootKey= "HKEY_LOCAL_MACHINE"):
        self.CurrentKey = None
        #注册表所有根键列表
        CWinReg.RootKeyList = {"HKEY_LOCAL_MACHINE":_winreg.HKEY_LOCAL_MACHINE, 
                            "HKEY_CLASSES_ROOT":_winreg.HKEY_CLASSES_ROOT, 
                            "HKEY_CURRENT_USER":_winreg.HKEY_CURRENT_USER, 
                            "HKEY_USERS":_winreg.HKEY_USERS, 
                            "HKEY_CURRENT_CONFIG":_winreg.HKEY_CURRENT_CONFIG }
        self.RootKey = CWinReg.RootKeyList[RootKey]
    def OpenKey(self, Key):
        #打开一个注册表子键
        self.CurrentKey = _winreg.OpenKey(self.RootKey,Key)
    def GetItemValue(self, ItemName=""):
        '''取得子键下 ItemName项的值,如果ItemName为空，那么取出来的是当前子键的默认值'''
        value = ""
        if ItemName == "":
            value = _winreg.QueryValue(self.CurrentKey,ItemName)
        else:
            #改函数返回的是一个tuple类型，索引0表示值，1表示itemname的类型
            value = _winreg.QueryValueEx(self.CurrentKey,ItemName)[0]
        return value
    def EnumSubkey(self):
        '''列举出当前根键下的所有子键名称，返回一个列表包含所有子键的名称'''
        SubkeyList = []
        SubkeyName = ""
        Go = True
        i = 0
        while Go:
            try:
                SubkeyName = _winreg.EnumKey(self.CurrentKey, i)
                SubkeyList.append(SubkeyName)
                i = i + 1
            except:
                Go = False
                break
        return SubkeyList
    def EnumItem(self):
        '''列举出当前根键下的所有Item（项目）名称，返回一个列表包含所有Item（项目）的名称,值，类型'''
        SubItemList = []
        SubkeyName = ""
        Go = True
        i = 0
        while Go:
            try:
                SubkeyName = _winreg.EnumValue(self.CurrentKey, i)
                SubItemList.append(SubkeyName)
                i = i + 1
            except:
                Go = False
                break
        return SubItemList
#定义CFtp类
class CFtp(ftplib.FTP):
	'''可以对FTP服务器进行交互式操作
	'''
	#CFtp的构造函数
	def __init__(self,Host,User,Password):
		self.Host = Host
		self.User = User
		self.Password = Password
		ftplib.FTP.__init__(self,Host,User,Password)
		prn("Connecting to the host:" + Host)
	def  PutFiles(self,Type,LocalFileName,RemoteFileName):
		#Type文件的传输类型
		#LocalFileName 本地文件名
		#RemoteFileName远程文件名
		prn("Uploading the file " + RemoteFileName)
		
		if Type =="asc":
			#以只读二进制打开文件
			ftplib.FTP.storlines(self,"STOR " + RemoteFileName, open(LocalFileName,'rb'))
		else:
			ftplib.FTP.storbinary(self,"STOR " + RemoteFileName, open(LocalFileName,'rb'))	
	
	def  GetFiles(self,Type,LocalFileName,RemoteFileName):
		#Type文件的传输类型
		#LocalFileName 本地文件名
		#RemoteFileName远程文件名
		prn("Downloading the file " + RemoteFileName)
		if Type =="asc":
			# wb==>以只读二进制写入文件
			ftplib.FTP.retrlines(self,'RETR ' + RemoteFileName, open(LocalFileName, 'wb').write)
		else:
			ftplib.FTP.retrbinary(self,'RETR ' + RemoteFileName, open(LocalFileName, 'wb').write)
	



#VSS库选择登陆界面
class CVSSLoginUI(QtGui.QDialog):
	def __init__(self, *args):
		QtGui.QWidget.__init__(self, *args)
		uic.loadUi(".\\PyQt4\\VSSLogin.ui", self)    
	@QtCore.pyqtSignature("")
	def on_CB_OK_clicked(self):
		print("Run here ,show dialog.")


#VSS项目文件夹选择浏览框
#class CVSSProjectUI(QtGui.QDialog):
#	def __init__(self, *args):
#		QtGui.QWidget.__init__(self, *args)
#		uic.loadUi(".\\PyQt4\\ProjectBrowse.ui", self)    
#	@QtCore.pyqtSignature("")
#定义CSourceSafe类
class CSourceSafe():
	#CSourceSafe的构造函数
	def __init__(self,SrcSafeIni = "",User = "",Password = ""):
		self.User = ""
		self.Password = ""
		if SrcSafeIni == "":            
			#CSourceSafe.SelectDatabase(self)
			CSourceSafe.SelectDatabase(self)
			return
		else:
			self.SrcSafeIni = SrcSafeIni            
		self.VSSObj = win32com.client.Dispatch("SourceSafe")
		self.VSSObj.Open(unicode(self.SrcSafeIni),unicode(User),unicode(Password))		
	def AddFiles(self,LocalPath,RemotePath):
		#Type文件的传输类型
		#LocalPath 本地文件名
		#RemotePath 远程文件名
		prn("Adding the file " + LocalPath + " to Visual Source Safe"  )
		VssItem = self.VSSObj.VSSItem(RemotePath)
		VssItem.Add(LocalPath)
	def GetFiles(self,LocalPath,RemotePath):
		#Type文件的传输类型
		#LocalPath 本地文件名
		#RemotePath 远程文件名
		LocalPath = unicode(LocalPath)
		RemotePath =(RemotePath)
		VssItem = self.VSSObj.VSSItem(RemotePath)
		#如果是个工程文件夹
		if VssItem.Type == 0:
			prn("Get the project " + VssItem.Name)
		else:
			prn("Get the file " + VssItem.Name)
		VssItem.Get(LocalPath,1)
		return 1
	def GetSpec(self,RemotePath):
		#RemotePath 远程文件名
		VssItem = self.VSSObj.VSSItem(RemotePath)
		prn(VssItem.Spec)
		prn(VssItem.VersionNumber)
		prn(VssItem.VersionNumber)
		return VssItem.Spec
	def GetNumVersions(self,RemotePath):
		try:
			VssItem = self.VSSObj.VSSItem(RemotePath)
		except:
			return 0
		return VssItem.VersionNumber
		
	def IsCheckedOut(self,VSSFile):
		VssItem = self.VSSObj.VSSItem(VSSFile)
		#0--没有CheckOut  1---CheckOut for other   2---CheckOut for me 
		res = VSSItem.IsCheckedOut
		if res==0:
			return False
		else:
			return True
	def CheckOut(self,VSSFile,LocalFile,Comment=""):
		prn("Check out the file:")
		prn("	VSS :" + VSSFile)
		prn("	Local: " + LocalFile)
		VssItem = self.VSSObj.VSSItem(VSSFile)
		VssItem.Checkout(Comment,LocalFile,0)		
	def CheckIn(self,VSSFile,LocalFile,Comment=""):
		prn("Check in the file:")
		prn("	VSS :" + VSSFile)
		prn("	Local: " + LocalFile)
		VssItem = self.VSSObj.VSSItem(VSSFile)
		VssItem.Checkin(Comment,LocalFile,0)		
	def UndoCheckOut(self,VSSFile,LocalFile,Comment=""):
		VssItem = self.VSSObj.VSSItem(VSSFile)
		VssItem.UndoCheckOut(LocalFile,0)			
	def SelectDatabase(self):
		'''弹出一个对话框，选择需要登陆的VSS数据库'''
		reg = CWinReg()
		reg.OpenKey("SOFTWARE\\Microsoft\\SourceSafe\\DataBases")
		#取得所有注册过的VSS库列表
		DBList = reg.EnumItem()
		app = QtGui.QApplication(sys.argv)
		Win = CVSSLoginUI()
		#把VSS库列表加入到下拉组合框中
		for db in DBList:
			print(unicode(db[0], "gbk"))
#			Win.COMBox_database.addItem (QtCore.QString(db[0]))
			Win.COMBox_database.addItem (unicode(db[0], "gbk"))
		Win.show()
		app.exec_()
		#sys.exit(app.exec_())
		#需要转换成Python string
		DBName = str(Win.COMBox_database.currentText())
		self.User = str(Win.EDIT_User.text())
		print("user is " + self.User)
		self.Password = str(Win.EDIT_Password.text())
		print("Password is " + self.Password)
		self.SrcSafeIni = reg.GetItemValue(str(DBName))
		return

#定义CTelnet类
class CTelnet(telnetlib.Telnet):
	#CTelnet的构造函数
	def __init__(self,Host,User,Password,Prompt="/smapupd>"):
		#Host 主机地址
		#User 用户名
		#Password 密码 
		#Prompt 命令提示符
		self.Result = ""
		self.Host = Host
		self.User = User
		self.Password = Password
		self.Prompt = Prompt
		telnetlib.Telnet.__init__(self,Host)
		#在Login:后输入
		telnetlib.Telnet.read_until(self,"ogin:")
		telnetlib.Telnet.write(self,User + "\n")
		#在Password:后输入密码
		telnetlib.Telnet.read_until(self,"assword:")
		telnetlib.Telnet.write(self,Password + "\n")
		telnetlib.Telnet.read_until(self,Prompt)
		prn("Connecting to the host [" + Host + "] successfully.")
	
	def __del__(self):
		pass
	def ExcuteCmd(self,Command):
		prn("Excuting the command:[" + Command + "]\n")
		#Command 需要执行命令	
		telnetlib.Telnet.write(self,Command)
		self.Result +=  telnetlib.Telnet.read_until(self,self.Prompt)
	def DisplayReturn(self):
		#显示返回的信息
		print self.Result
		

#定义CZip类
class CZip(zipfile.ZipFile):
	'''
	'''
	def __init__(self,FileName,ArcName=""):
		self.FileName = FileName
		self.ArcName = ArcName
		prn("Create compressed file " + self.ArcName )
		CZip.Compress(self,FileName,ArcName)
		prn("Create successfully")
	def Compress(self,FileName,ArcName):	
		absPath = os.path.abspath(FileName)
		WorkDir = ''
		#得到给出的路径最后的文件名或目录名
		CurrentSrc = os.path.split(absPath)[1]
		
		if os.path.isdir(absPath):
			WorkDir = absPath
			CurrentSrc = '.\\'
		else:
			WorkDir = os.path.dirname(absPath)
		
		OldWorDir = os.getcwd()
		#设置当前工作目录
		os.chdir(WorkDir)
		#建立一个压缩包
		zip = zipfile.ZipFile(ArcName,'w',zipfile.ZIP_DEFLATED)
		CZip.ZipFileR(self,CurrentSrc,zip)
		zip.close()
		os.chdir(OldWorDir)
		return 1
	def ZipFileR(self,FileName,zip):
		''' 在调用这个函数之前,首先需要调用os.chdir()
			这个函数来改变当前的工作目录,否则压缩出来的压缩包是包含路径的
			在调用完成以后需要把工作目录设置回原来的
			该函数递归调用压缩目录
		'''
		if os.path.isdir(FileName):			
			#对每一个文件目录进行循环
			for fileitem in os.listdir(FileName):
				CurFilePath = FileName + '\\' + fileitem
				if os.path.isdir(CurFilePath):	
					CZip.ZipFileR(self.CurFilePath,zip)
				else:
					prn ('	Adding the file ==>> ' + fileitem)
					zip.write(CurFilePath)
		else:
			prn ('	Adding the file ==>> ' + FileName)
			zip.write(FileName)

	def __del__(self):
		pass
class CPowerBuilder():
	def __init__(self,PBPath=r"D:\Program Files\Sybase\PowerBuilder 8.0\pb80.exe",PBVersioon=80):
		self.PBPath = PBPath
		self.PBVersioon = PBVersioon
		self.PB_WorkSpace = "PBW_Temp.pbw"
		CPowerBuilder.SetPBTCount(self,1)
	def SetPBTCount(self,PBTCount=1):
		self.PBLList=[]
		self.PBLPath=[]
		self.AppName=[]
		self.CompileInfo=[]
		self.AppPBL=[]
		for i in range(0,PBTCount):
				self.PBLList.append([])
				self.PBLPath.append([])
				self.AppName.append("")
				self.CompileInfo.append("")
				self.AppPBL.append("")
	def SetApp(self,AppName,AppPBL,PBTIndex=0):
		'''
		设置应用程序对象的名称，应用程序对象所在的PBL
		'''	
		self.AppName[PBTIndex] = AppName
		self.AppPBL[PBTIndex] = AppPBL
	def SetPBL(self,PBLPath,PBLList,PBTIndex=0):
		'''
		设置PBT包含有那些PBL的文件
		'''
		self.PBLList[PBTIndex] = PBLList
		self.PBLPath[PBTIndex] = PBLPath
		self.PBWPath = self.PBLPath[0] 
	def SetCompileInfo(self,ExeFile="smapexec.exe",CompileFlag = "0,0,0,2,0,0",
		PBRFile="smap.pbr",	CompName="Huawei Technologies Co., Ltd.", 
		ProductName="UIN PPS(C+G)",		Desc="Huawei smapexec.exe file", 
		Copyright="Copyright(C) 1995-2008 Huawei Technologies Co., Ltd.",		
		Version="EHZV1.0D100",PBTIndex=0):
		'''
		设置编译工程对象的相关信息
		'''
		self.PB_WorkSpace = "PBW_" + Version + ".pbw"
		self.CompileInfo[PBTIndex]  = 'EXE:'
		self.CompileInfo[PBTIndex] += self.PBLPath[PBTIndex]  + "\\" + ExeFile + ","
		self.CompileInfo[PBTIndex] += self.PBLPath[PBTIndex]  + "\\" +  PBRFile + ",0,1\n" 
		#配置信息
		self.CompileInfo[PBTIndex] += 'CMP:' + CompileFlag + '\n'	
		#公司信息
		self.CompileInfo[PBTIndex] += 'COM:' + CompName + '\n'
		#描述信息
		self.CompileInfo[PBTIndex] += 'DES:' + Desc+ '\n'
		#授权信息
		self.CompileInfo[PBTIndex] += 'CPY:' + Copyright+ '\n'	
		#产品名称信息
		self.CompileInfo[PBTIndex] += 'PRD:' + ProductName + '\n'	
		#版本信息
		self.CompileInfo[PBTIndex] += 'VER:' + Version + '\n'
		#PBD文件列表
		PBLCount = len(self.PBLList[PBTIndex])
		for j in range(0,PBLCount):
			self.CompileInfo[PBTIndex] += 'PBD:' + self.PBLPath[PBTIndex] + "\\" + self.PBLList[PBTIndex][j] + ",,1"     + '\n'
		CPowerBuilder.GenCompileObj(self,PBTIndex)
	def GenCompileObj(self,PBTIndex):
		'''
		生成一个可以编译的工程对象，然后导入到PBL对象中
		'''
		#保存当前的工作路径
		OldWorDir = os.getcwd()
		#设置当前工作目录
		os.chdir(self.PBLPath[PBTIndex])
				
		SyntaxFile = self.AppName[PBTIndex] + ".srj"
		#app_smap = self.PBLPath[PBTIndex] + "\\" + SyntaxFile
		#开始写app_smap.srj文件
		f_app_smap = open(SyntaxFile,'w')
		tmpstr = '$PBExportHeader$' + SyntaxFile + '\n'
		f_app_smap.writelines(tmpstr)		
		f_app_smap.writelines(self.CompileInfo[PBTIndex])	
		#关闭文件
		f_app_smap.close()
		
		#生成ORC语法文件
		ORCFileName="ImportObj.orc"
		ORCFile = open(ORCFileName,"w")
		tmpstr = 'session begin pborc' + str(self.PBVersioon) + '.dll \n'		
		ORCFile.writelines(tmpstr)
		
		#===============================begin
		tmpstr = 'set liblist begin' + '\n'
		ORCFile.writelines(tmpstr)				
		#写PBL列表
		for pbl in self.PBLList[PBTIndex]:
			tmpstr = pbl +" ,1 \n"
			ORCFile.writelines(tmpstr)
		tmpstr = 'set liblist end' + '\n'
		ORCFile.writelines(tmpstr)
		#===============================end
		
		tmpstr = 'set application ' + self.AppPBL[PBTIndex] + ","+ self.AppName[PBTIndex] + '\n'
		ORCFile.writelines(tmpstr)
		
		tmpstr = 'import ' + SyntaxFile +  "," + self.AppPBL[PBTIndex] +'\n'
		ORCFile.writelines(tmpstr)
		
		tmpstr = 'session end' + '\n'
		ORCFile.writelines(tmpstr)
		ORCFile.close()
		
		tmpstr = OldWorDir + "\\pborcaw\\pborcaA.exe " + ORCFileName
		os.system(tmpstr)
		
		#DelCmd = "del " + self.PBLPath[PBTIndex] + "\\" +SyntaxFile
		#os.system(DelCmd)
		
		#工作路径还原回来
		os.chdir(OldWorDir)
	def RunPB(self):
		if self.PBVersioon == 60 :
			#保存当前的工作路径
			#OldWorDir = os.getcwd()
			#WorkDir = os.path.dirname(self.PBPath)
			#设置当前工作目录
			#os.chdir(WorkDir)
			PBRun = self.PBPath
			os.system(PBRun)
			#还原工作目录
			#os.chdir(OldWorDir)
			return
		#保存当前的工作路径
		OldWorDir = os.getcwd()
		#设置当前工作目录
		os.chdir(self.PBWPath)
		#开始写工作区文件
		f_PBW = open(self.PB_WorkSpace,'w')
		tmpstr = 'Save Format v3.0(19990112)' + '\n'
		f_PBW.writelines(tmpstr)	
		tmpstr = '@begin Targets' + '\n'
		f_PBW.writelines(tmpstr)	
		PBTCount = len(self.PBLList)
		#循环把PBT文件合入到PBW文件中
		for i in range(0,PBTCount):
			#生成PBT文件
			PBTFileName = self.AppName[i] + ".pbt"
			f_PBT = open(PBTFileName,"w")
			tmpstr = 'Save Format v3.0(19990112)' + '\n'
			f_PBT.writelines(tmpstr)
			tmpstr = 'appname "' + self.AppName[i] + '";\n'
			f_PBT.writelines(tmpstr)
			tmpstr = 'applib "' + self.AppPBL[i] + '";\n'
			f_PBT.writelines(tmpstr)
			delimiter = ";"
			tmpstr = 'liblist "' + delimiter.join(self.PBLList[i] ) + '";\n'
			f_PBT.writelines(tmpstr)
			tmpstr = 'type "pb";' + '\n'
			f_PBT.writelines(tmpstr)
			f_PBT.close()
			#把PBT文件合入到PBW文件中
			tmpstr = str(i) + ' "' + PBTFileName + '";\n'
			f_PBW.writelines(tmpstr)	
		tmpstr = '@end;' + '\n'
		f_PBW.writelines(tmpstr)	
		f_PBW.close()		
		#工作路径还原回来
		os.chdir(OldWorDir)
		
		PBRun ='"'+ self.PBPath  + '" /w ' +  self.PBWPath + "\\" +self.PB_WorkSpace
		os.system(PBRun)
def CheckWorkDir(LocalDir):	
	if not os.path.exists(LocalDir):		
		os.makedirs(LocalDir)
	return 1
def ArcEPPCFiles_BAK():
	VssEPPCPath = r"\\192.168.1.4\eppcv300r003c04b090\SourceSafe.ini"
	VssUser = "xiedaolin"
	VssPass = "xiedaolin"
	
	VssPath_Archive = r"\\192.168.1.4\PowerBuilder_VSS\SourceSafe.ini"
	ArcPath_MDD = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/1.MDD"
	ArcPath_RUN = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/2.RUN"
	ArcPath_SRC = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/3.SRC"
	ArcPath_UPD = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/4.UPD"
	
	Host = "192.168.1.5"	#服务器IP地址
	CmdTip="/smapupd>"	#在不同的环境下,命令提示符不一样.
	#根据不同的平台设置不同的命令提示符号
	if Host=="192.168.1.5" :
		CmdTip="/smapupd>"
	elif Host=="192.168.1.3" :
		CmdTip="Sun60%"
	elif Host=="192.168.1.16" :
		CmdTip="E4500%"
	elif Host=="192.168.1.9" :
		CmdTip="/smapupd>"
	elif Host=="192.168.1.11" :
		CmdTip="/smapupd>"
	elif Host=="192.168.1.13" :
		CmdTip="e450%"
	else:
		CmdTip = ">"
	TelUser = "smapupd"	#登陆的用户名
	TelPass = "qwer][po"	#登陆的密码
	
	PB_RUN = r'"d:\program files\Sybase\PowerBuilder 8.0\pb80.exe " /w  '
	PB_WorkSpace_Name = "SMAP_RUN_Archive.pbw"
	#完整的版本号格式 EPPCV***R***C**B**N (N = 1,2,3,...)
	ProjVerPrefix  = "EPPCV300R003C04B09"
	ProjVersuffix  = "2"	#表示本版本第几轮
	ProjVersion    = ProjVerPrefix + ProjVersuffix
	UPD_FileName   = "CIN_" + ProjVersion + "_SMAP_UPD.BIN"
	RUN_FileName   = "CIN_" + ProjVersion + "_SMAP_RUN.zip"
	SRC_FileName   = "CIN_" + ProjVersion + "_SMAP_SRC.zip"

	LocalTempPath = "d:\\temp\\" + ProjVersion
	UPD_DIRNAME    = "UPD"
	RUN_DIRNAME    = "RUN"
	SRC_DIRNAME    = "SRC"
	TMP_DIRNAME    = "TMP"
	

	#本地的归档全路径
	LocalPath_RUN = LocalTempPath + "\\" + RUN_DIRNAME
	LocalPath_SRC = LocalTempPath + "\\" + SRC_DIRNAME
	LocalPath_UPD = LocalTempPath + "\\" + UPD_DIRNAME
	LocalPath_TMP = LocalTempPath + "\\" + TMP_DIRNAME
	LocalPath_CUR = LocalTempPath + "\\" + TMP_DIRNAME
	
	CheckWorkDir(LocalPath_RUN)
	CheckWorkDir(LocalPath_SRC)
	CheckWorkDir(LocalPath_UPD)
	CheckWorkDir(LocalPath_TMP)
	
	RemotePath = "xdlupd"	#归档包服务器上的路径

	#压缩的文件名和压缩后的文件名对应关系
	ArcFileListOri = ["smidll.dll","cygwin1.dll","encode.dll","SmapDll.dll","ConvertToUni.dll","gzip.exe","smapexec.exe","servicecfg.cfg","system.pbd","smap.pbd","public.pbd","public_p.pbd","public_g.pbd","public_dddw.pbd","eppc.pbd","up.bmp","down.bmp","hwhelp.dat","hweppchelp.dat","PPC_SMAP_HELP.chm","base_smap_help.chm","huawei.bmp",    "huawei.ico",   "WordMapping.dat","eppc_a.pbd","eppc_b.pbd","eppc_c.pbd"]
	ArcFileListZip = ["smidll.zip","cygwin1.zip","encode.zip","SmapDll.zip","ConvertToUni.zip","gzip.zip","smapexec.zip","servicecfg.zip","system.zip","smap.zip","public.zip","public_p.zip","public_g.zip","public_dddw.zip","eppc.zip","up.zip","down.zip","hwhelp.zip","hweppchelp.zip","PPC_SMAP_HELP.zip","base_smap_help.zip","huaweibmp.zip","huaweiico.zip","WordMapping.zip","eppc_a.zip","eppc_b.zip","eppc_c.zip"]
	
	EPPCProjPath = u"$/EPPCV300R003C04b09/Develop/01.CI/1.7 Code/SMS/OCS&IN EPPCV300R003C04B090/SMAP"
	BASEProjPath = "$/EPPCV300R003C04b09/Develop/01.CI/1.7 Code/SMS/OCS&IN EPPCV300R003C04B090/BASELINE/CIN_UBASE_SMAP_EN_V2.0D340/E_SMAPV1.2"
	#生成SourceSafe对象
	#取得文件
	vssobj = CSourceSafe(VssEPPCPath,VssUser,VssPass)
	vssobj.GetFiles(LocalPath_RUN,EPPCProjPath)
	vssobj.GetFiles(LocalPath_RUN,BASEProjPath)
	
	print ("Archive EPPC files.")


def ArcEPPCFiles(Type = "SMAP"):
	VssEPPCPath = r"\\192.168.1.4\eppcv300r003c05b11\SourceSafe.ini"
	VssUser = "xiedaolin"
	VssPass = "xiedaolin"
		
	VssPath_Archive = r"\\192.168.1.4\ArchiveVSS\SourceSafe.ini"
	ArcPath_MDD = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/1.MDD"
	ArcPath_RUN = unicode("$/01.CIN/EPPCV300R003C05B110/验收版本/1.EPPCV300R003C05B110-验收2/5.Software/4.CMP/2.RUN","utf-8")
	ArcPath_SRC = unicode("$/01.CIN/EPPCV300R003C05B110/验收版本/1.EPPCV300R003C05B110-验收2/5.Software/4.CMP/3.SRC","utf-8")
	ArcPath_UPD = unicode("$/01.CIN/EPPCV300R003C05B110/验收版本/1.EPPCV300R003C05B110-验收2/5.Software/4.CMP/4.UPD","utf-8")
	
	Host = "192.168.1.5"	#服务器IP地址
	CmdTip="/smapupd>"	#在不同的环境下,命令提示符不一样.
	#根据不同的平台设置不同的命令提示符号
	if Host=="192.168.1.5" :
		CmdTip="/smapupd>"
	elif Host=="192.168.1.3" :
		CmdTip="Sun60%"
	elif Host=="192.168.1.16" :
		CmdTip="E4500%"
	elif Host=="192.168.1.9" :
		CmdTip="/smapupd>"
	elif Host=="192.168.1.11" :
		CmdTip="/smapupd>"
	elif Host=="192.168.1.13" :
		CmdTip="e450%"
	else:
		CmdTip = ">"
	TelUser = "smapupd"	#登陆的用户名
	TelPass = "qwer][po"	#登陆的密码
	
	#完整的版本号格式 EPPCV***R***C**B**N (N = 1,2,3,...)
	ProjVerPrefix  = "EPPCV300R003C05B11"
	ProjVersuffix  = "1"	#表示本版本第几轮
	ProjVersion    = ProjVerPrefix + ProjVersuffix
	UPD_FileName   = "CIN_" + ProjVersion + "_" + Type + "_UPD.BIN"
	RUN_FileName   = "CIN_" + ProjVersion + "_" + Type + "_RUN.zip"
	SRC_FileName   = "CIN_" + ProjVersion + "_" + Type + "_SRC.zip"

	LocalTempPath = "d:\\temp\\" + ProjVersion + Type 
	UPD_DIRNAME  = "UPD"
	RUN_DIRNAME  = "RUN"
	SRC_DIRNAME  = "SRC"
	TMP_DIRNAME = "TMP"
	CUR_DIRNAME  = Type + "本轮修改文件"

	#本地的归档全路径
	LocalPath_RUN = LocalTempPath + "\\" + RUN_DIRNAME
	LocalPath_SRC = LocalTempPath + "\\" + SRC_DIRNAME
	LocalPath_UPD = LocalTempPath + "\\" + UPD_DIRNAME
	LocalPath_TMP = LocalTempPath + "\\" + TMP_DIRNAME
	LocalPath_CUR = LocalTempPath + "\\" + CUR_DIRNAME
	
	os.system("del " + LocalPath_UPD + "\\*.* /F /Q \n")
	
	CheckWorkDir(LocalPath_RUN)
	CheckWorkDir(LocalPath_SRC)
	CheckWorkDir(LocalPath_UPD)
	CheckWorkDir(LocalPath_TMP)
	CheckWorkDir(LocalPath_CUR)
	
	#从VSS库上取文件
	if Type == "SMAP" :
		EPPCProjPath = "$/EPPCV300R003C04b09/Develop/01.CI/1.7 Code/SMS/OCS&IN EPPCV300R003C04B090/SMAP"
		BASEProjPath = "$/EPPCV300R003C04b09/Develop/01.CI/1.7 Code/SMS/OCS&IN EPPCV300R003C04B090/BASELINE/CIN_UBASE_SMAP_EN_V2.0D340/E_SMAPV1.2"
	else:
		#CMP
		EPPCProjPath = "$/EPPCV300R003C05B11/1.开发/01.配置项/1.7 代码/SMS/CMP"
		BASEProjPath = ""
			
	v = CSourceSafe(VssEPPCPath,VssUser,VssPass)
	
	if Type == "SMAP":
		v.GetFiles(unicode(LocalPath_RUN),BASEProjPath)
	#表示用gbk解码，转换成unicode编码
	v.GetFiles(LocalPath_RUN,unicode(EPPCProjPath,"utf-8"))
	v.GetFiles(LocalPath_RUN,unicode(EPPCProjPath,"utf-8"))
	v.GetFiles(LocalPath_SRC,unicode(EPPCProjPath,"utf-8"))
	v.GetFiles(LocalPath_SRC,unicode(EPPCProjPath,"utf-8"))
	
	PB6 = CPowerBuilder(r"D:\Sybase\PB6\pb60.exe",60)
	PB6.RunPB()
	
	#压缩的文件名和压缩后的文件名对应关系
	if Type == "SMAP" :
		ArcFileListOri = ["smidll.dll","cygwin1.dll","encode.dll","SmapDll.dll","ConvertToUni.dll","gzip.exe","smapexec.exe","servicecfg.cfg","system.pbd","smap.pbd","public.pbd","public_p.pbd","public_g.pbd","public_dddw.pbd","eppc.pbd","up.bmp","down.bmp","hwhelp.dat","hweppchelp.dat","PPC_SMAP_HELP.chm","base_smap_help.chm","huawei.bmp",    "huawei.ico",   "WordMapping.dat","eppc_a.pbd","eppc_b.pbd","eppc_c.pbd"]
		ArcFileListZip = ["smidll.zip","cygwin1.zip","encode.zip","SmapDll.zip","ConvertToUni.zip","gzip.zip","smapexec.zip","servicecfg.zip","system.zip","smap.zip","public.zip","public_p.zip","public_g.zip","public_dddw.zip","eppc.zip","up.zip","down.zip","hwhelp.zip","hweppchelp.zip","PPC_SMAP_HELP.zip","base_smap_help.zip","huaweibmp.zip","huaweiico.zip","WordMapping.zip","eppc_a.zip","eppc_b.zip","eppc_c.zip"]
	else:
		ArcFileListOri = ["emc_lib.dll","encode.dll","SmapDll.dll","e_mcb.dat","hwhelp.dat","cardcomm.pbd","cmp.pbd","fun.pbd","grant.pbd","precharge.pbd","report.pbd","report_cmp_ppip.pbd","resource.pbd","subserv.pbd","CMP_Help.chm","cmpexec.exe","pbin760.dll","gzip.dll","filedecode.exe","fileencode.exe","huawei.bmp"      ,"huawei.ico"      ,"seedfile_gzip.exe","zipseedfile.dll","SeedFile.exe"]
		ArcFileListZip = ["emc_lib.zip","encode.zip","SmapDll.zip","e_mcb.zip","hwhelp.zip","cardcomm.zip","cmp.zip","fun.zip","grant.zip","precharge.zip","report.zip","report_cmp_ppip.zip","resource.zip","subserv.zip","CMP_Help.zip","cmpexec.zip","pbin760.zip","gzip.zip","filedecode.zip","fileencode.zip","huaweibmp.zip","huaweiico.zip","seedfile_gzip.zip","zipseedfile.zip","SeedFile.zip"]

	Count = len(ArcFileListOri)
	#按照列表进行压缩
	for i in range(0,Count):
		z = CZip(LocalPath_RUN + "\\" + ArcFileListOri[i],  LocalPath_TMP + "\\" + ArcFileListZip[i])
	
	RemotePath = "xdlupd"
	
	#把压缩包传输到服务器上
	ftp = CFtp("192.168.1.5","smapupd","qwer][po")
	ftp.mkd(RemotePath)
	ftp.cwd(RemotePath)
	
	for i in range(0,Count):
		ftp.PutFiles("bin",LocalPath_TMP + "\\" + ArcFileListZip[i],ArcFileListZip[i])
	ftp.PutFiles("asc",LocalPath_RUN + "\\install_upd.sh","install_upd.sh")	
	ftp.PutFiles("asc",LocalPath_RUN + "\\version.ini","version.ini")
	ftp.cwd("..")
	
	t = CTelnet("192.168.1.5","smapupd","qwer][po")
	cmdstr = "rm -rf " + UPD_FileName + " \n" 
	t.ExcuteCmd(cmdstr)
	cmdstr = "./makeinstall.sh " + RemotePath + " install_upd.sh " + UPD_FileName +" \n" 
	t.ExcuteCmd(cmdstr)
	t.DisplayReturn()
	cmdstr = "rm -rf " + RemotePath + " \n" 
	t.ExcuteCmd(cmdstr)
	
	#把生成好的文件Get回来
	ftp.GetFiles("bin",LocalPath_UPD + "\\" + UPD_FileName, UPD_FileName )
	ftp.delete( UPD_FileName)
	
	#编译完成后,清理不需要的文件	
	prn("delte the file *.scc,*.pbl")
	DelCmd = "del " + LocalPath_RUN + "\\" + "*.scc"
	os.system(DelCmd)
	DelCmd = "del " + LocalPath_SRC+ "\\"  + "*.scc"
	os.system(DelCmd)
	DelCmd = "del " + LocalPath_RUN + "\\" + "*.pbl"
	os.system(DelCmd)
	
	z = CZip(LocalPath_RUN,  LocalPath_UPD+ "\\" + RUN_FileName)
	z = CZip(LocalPath_SRC,  LocalPath_UPD+ "\\" + SRC_FileName)
	
	#把生成号的压缩包放入归档库	
	VssArc = CSourceSafe(VssPath_Archive,VssUser,VssPass)
	#把RUN包Check In 到归档库
	if VssArc.GetNumVersions(ArcPath_RUN + "/"  + RUN_FileName) > 0 :
		VssArc.CheckOut(ArcPath_RUN + "/"  + RUN_FileName,LocalPath_TMP + "\\" + RUN_FileName)
		VssArc.CheckIn(ArcPath_RUN + "/"  + RUN_FileName,LocalPath_UPD + "\\" + RUN_FileName)
	else:
		VssArc.AddFiles( LocalPath_UPD+ "\\" + RUN_FileName,ArcPath_RUN)
	
	#把SRC包Check In 到归档库	
	if VssArc.GetNumVersions(ArcPath_SRC + "/"  + SRC_FileName) > 0 :
		VssArc.CheckOut(ArcPath_SRC + "/"  + SRC_FileName,LocalPath_TMP + "\\" + SRC_FileName)
		VssArc.CheckIn(ArcPath_SRC + "/"  + SRC_FileName,LocalPath_UPD + "\\" + SRC_FileName)
	else:
		VssArc.AddFiles( LocalPath_UPD+ "\\" + SRC_FileName,ArcPath_SRC)
	
	#把UPD包Check In 到归档库	
	if VssArc.GetNumVersions(ArcPath_UPD + "/"  + UPD_FileName) > 0 :
		VssArc.CheckOut(ArcPath_UPD + "/"  + UPD_FileName,  LocalPath_TMP + "\\" + UPD_FileName)
		VssArc.CheckIn(ArcPath_UPD + "/"  + UPD_FileName,     LocalPath_UPD + "\\" + UPD_FileName)
	else:
		VssArc.AddFiles( LocalPath_UPD+ "\\" + UPD_FileName,  ArcPath_UPD)	
def PythonMain():	
	ArcEPPCFiles("CMP")
	os.system('pause')		#系统暂停
	return 1	
def Test():
	#ftp = CFtp("192.168.1.5","smapupd","qwer][po")
	#ftp.GetFiles("bin","C:\\base_smap_help.zip","base_smap_help.zip")
	#t = CTelnet("192.168.1.5","smapupd","qwer][po")
	#t.ExcuteCmd("ls -l \n")
	#t.ExcuteCmd("mkdir xxxx \n")
	#t.DisplayReturn()
	#t.ExcuteCmd("exit \n")
	#t.DisplayReturn()
	#z = CZip("Document","f:\Document.zip")
#	VssEPPCPath= r"\\192.168.1.4\eppcv300r003c05b11\SourceSafe.ini"
#	VssUser = "xiedaolin"
#	VssPass = "xiedaolin"
#	v=CSourceSafe(VssEPPCPath,VssUser,VssPass)
#	prn (v.GetSpec(unicode("$/EPPCV300R003C05B11/1.开发/01.配置项/1.7 代码/SMS/SMAP/eppc_a.pbl","gbk")))
	#pb = CPowerBuilder()
	#pb.SetPBTCount(2)
	#pb.SetApp("app_smap","smap.pbl",0)
	#pb.SetApp("autoupdate","autoupdate.pbl",1)
	#L0=["smap.pbl","system.pbl","eppc.pbl","eppc_a.pbl","eppc_b.pbl","eppc_c.pbl","public.pbl","public_dddw.pbl","public_g.pbl","public_p.pbl"]
	#L1=["autoupdate.pbl"]
	#pb.SetPBL( "d:\\temp\\RunXXX",L0,0)
	#pb.SetPBL( "d:\\temp\\RunXXX",L1,1)
	#pb.SetCompileInfo(ExeFile="smapexec.exe", CompileFlag = "0,0,0,2,0,0", PBRFile="smap.pbr",		CompName="Huawei Technologies Co., Ltd.",  ProductName="UIN PPS(C+G)",		Desc="Huawei smapexec.exe file", Copyright="Copyright(C) 1995-2008 Huawei Technologies Co., Ltd.",		Version="EPPCV300R003C04b09",  PBTIndex=0)
	#pb.SetCompileInfo(ExeFile="smap.exe",         CompileFlag = "1,0,0,2,0,0", PBRFile="",	                    CompName="Huawei Technologies Co., Ltd.",  ProductName="UIN PPS(C+G)",		Desc="Huawei smap.exe file",         Copyright="Copyright(C) 1995-2008 Huawei Technologies Co., Ltd.",		Version="EPPCV300R003C04b09",  PBTIndex=1)
	#pb.RunPB()
	#ArcEPPCFiles()
#    reg = CWinReg()
#    reg.OpenKey("Software\sybase\Powerbuilder\8.0")
#    print reg.GetItemValue("location")
#    print reg.EnumSubkey()
#    print reg.EnumItem()
    v = CSourceSafe()
    print ("the end.")
if __name__ == '__main__' :
	Test()
#	PythonMain()
	
