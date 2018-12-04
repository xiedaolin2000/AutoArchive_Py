# -*- coding: gb2312 -*-
#==========================================================================
#			SMAP自动归档Python脚本
#描述:
#	该功能实现了,把文件从指定的VSS上取文件下来,打开PB工具编译,编译完成后
#	对指定的文件按照要求进行压缩,把压缩后的文件上传到Unix服务器上进行打包,生成一个升级包
#	把生成后的升级包取下来.
#
#作者:	谢道林
#日期:	2008-07-28
#历史:
#	
#==========================================================================
import getpass
import sys
import os
import socket
import telnetlib	#为了使用Telnet功能
import ftplib		#启用FTP功能
import zipfile 		#启用压缩功能
import distutils.file_util	#使用一些文件操作函数功能
#导入win32com库 SourceSafe.0
import win32com.client

def DebugInfo():
	return 1
def prn(str):
	'''
	打印提示信息
	'''
	print(str)
	return 1

gVssPath = r"\\192.168.1.4\eppcv300r003c04b090\SourceSafe.ini"
gVssUser = "xiedaolin"
gVssPass = "xiedaolin"

#归档库上各个包存放的路径
#字符串前面加一个字母r表示可以不使用转义字符.
gVssPath_Archive = r"\\192.168.1.4\PowerBuilder_VSS\SourceSafe.ini"
gArcPath_MDD = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/1.MDD"
gArcPath_RUN = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/2.RUN"
gArcPath_SRC = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/3.SRC"
gArcPath_UPD = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/4.UPD"


gHost = "192.168.1.5"	#服务器IP地址
gCmdTip="/smapupd>"	#在不同的环境下,命令提示符不一样.
#根据不同的平台设置不同的命令提示符号
if gHost=="192.168.1.5" :
	gCmdTip="/smapupd>"
elif gHost=="192.168.1.3" :
	gCmdTip="Sun60%"
elif gHost=="192.168.1.16" :
	gCmdTip="E4500%"
elif gHost=="192.168.1.9" :
	gCmdTip="/smapupd>"
elif gHost=="192.168.1.11" :
	gCmdTip="/smapupd>"
elif gHost=="192.168.1.13" :
	gCmdTip="e450%"
else:
	gCmdTip = ">"
gTelUser = "smapupd"	#登陆的用户名
gTelPass = "qwer][po"	#登陆的密码

gPB_RUN = r'"d:\program files\Sybase\PowerBuilder 8.0\pb80.exe " /w  '
gPB_WorkSpace_Name = "SMAP_RUN_Archive.pbw"
#完整的版本号格式 EPPCV***R***C**B**N (N = 1,2,3,...)
gProjVerPrefix  = "EPPCV300R003C04B09"
gProjVersuffix  = "2"	#表示本版本第几轮
gProjVersion    = gProjVerPrefix + gProjVersuffix
gUPD_FileName   = "CIN_" + gProjVersion + "_SMAP_UPD.BIN"
gRUN_FileName   = "CIN_" + gProjVersion + "_SMAP_RUN.zip"
gSRC_FileName   = "CIN_" + gProjVersion + "_SMAP_SRC.zip"

gLocalTempPath = r"d:\temp\TMP_" + gProjVersion
gUPD_DIRNAME    = "UPD"
gRUN_DIRNAME    = "RUN"
gSRC_DIRNAME    = "SRC"
gTMP_DIRNAME    = "TMP"

#本地的归档全路径
gLocalPath_RUN = gLocalTempPath + "\\" + gRUN_DIRNAME
gLocalPath_SRC = gLocalTempPath + "\\" + gSRC_DIRNAME
gLocalPath_UPD = gLocalTempPath + "\\" + gUPD_DIRNAME
gLocalPath_TMP = gLocalTempPath + "\\" + gTMP_DIRNAME



gRemotePath = "xdlupd"	#归档包服务器上的路径

#压缩的文件名和压缩后的文件名对应关系
gArcFileListOri = ["smidll.dll","cygwin1.dll","encode.dll","SmapDll.dll","ConvertToUni.dll","gzip.exe","smapexec.exe","servicecfg.cfg","system.pbd","smap.pbd","public.pbd","public_p.pbd","public_g.pbd","public_dddw.pbd","eppc.pbd","up.bmp","down.bmp","hwhelp.dat","hweppchelp.dat","PPC_SMAP_HELP.chm","base_smap_help.chm","huawei.bmp",    "huawei.ico",   "WordMapping.dat","eppc_a.pbd","eppc_b.pbd","eppc_c.pbd"]
gArcFileListZip = ["smidll.zip","cygwin1.zip","encode.zip","SmapDll.zip","ConvertToUni.zip","gzip.zip","smapexec.zip","servicecfg.zip","system.zip","smap.zip","public.zip","public_p.zip","public_g.zip","public_dddw.zip","eppc.zip","up.zip","down.zip","hwhelp.zip","hweppchelp.zip","PPC_SMAP_HELP.zip","base_smap_help.zip","huaweibmp.zip","huaweiico.zip","WordMapping.zip","eppc_a.zip","eppc_b.zip","eppc_c.zip"]

#=============================================================================================================================================================

#一生成以后就是VSSDatabase COM对象
prn('初始化COM环境... 生成VSS对象')
gVssDatabaseObj = win32com.client.Dispatch("SourceSafe")

prn('生成FTP操作对象 ...')
gFtpObj = ftplib.FTP(gHost,gTelUser,gTelPass)

prn('生成Telnet操作对象 ...')
gTelnetObj = telnetlib.Telnet(gHost)


def VssGetFile(LocalPath,Vss_path):
	VssItem = gVssDatabaseObj.VSSItem(Vss_path)
	for item in VssItem.GetItems():
		#如果是个工程文件夹
		if item.Type == 0:
			prn(u"进入VSS目录==>" + "/" +  item.Name)
			VssGetFile(LocalPath + u"\\"+ item.Name,Vss_path + "/" +  item.Name)			
		else:	#是文件
			prn(u"取得文件==>" + item.Name)
			#VSSFLAG_KEEPYES  让文件是可写状态
			item.Get(LocalPath + u"\\"+ item.Name,1)
	return 1
def ExecVssPutFile():
	prn('是否需要把归档包自动放到归档库上.')
	prn('注意:')
	prn('1.要正确设置归档库的路径.' )
	prn('2.设置的路径中必须是空目录,否则存放失败.')
	inputstr = raw_input("是否继续?[Y/N,Y--是,其它--否]:")
	inputstr = inputstr.upper()	
	if inputstr != "Y":
		return 0
	
	#需要重新生成一个COM对象,使用原来的会有问题.
	ArchiveVSS_DB_OBJ = win32com.client.Dispatch("SourceSafe")
	ArchiveVSS_DB_OBJ.Open(gVssPath_Archive,gVssUser,gVssPass)
	
	LocalUpd = gLocalTempPath + "\\" + gUPD_DIRNAME + "\\"
	#把RUN包放到VSS库上
	prn('把 ' + gRUN_FileName + '文件,上传到VSS库,路径' + gArcPath_RUN)
	prn('gArcPath_RUN = ' + gArcPath_RUN)
	VssProject = ArchiveVSS_DB_OBJ.VSSItem(gArcPath_RUN)
	VssProject.Add(LocalUpd + gRUN_FileName , 'Xiedaolin',0)
	
	#把SRC包放到VSS库上
	prn('把 ' + gSRC_FileName + '文件,上传到VSS库,路径' + gArcPath_SRC)
	VssProject = ArchiveVSS_DB_OBJ.VSSItem(gArcPath_SRC)
	VssProject.Add(LocalUpd + gSRC_FileName , 'Xiedaolin',0)
	
	#把UPD包放到VSS库上
	prn('把 ' + gUPD_FileName + '文件,上传到VSS库,路径' + gArcPath_UPD)
	VssProject = ArchiveVSS_DB_OBJ.VSSItem(gArcPath_UPD)
	VssProject.Add(LocalUpd + gUPD_FileName , 'Xiedaolin',0)
	return 1
def FtpGetFile(Local,Remote,Mod):	
	if Mod =="asc":
		# wb==>以只读二进制打开文件
		gFtpObj.retrlines('RETR ' + Remote, open(Local, 'wb').write)
	else:
		gFtpObj.retrbinary('RETR ' + Remote, open(Local, 'wb').write)
	return 1
def ExecFtpGetFile():
	LocalUpd   = gLocalTempPath + "\\" + gUPD_DIRNAME + "\\"
	LocalFile  = LocalUpd + gUPD_FileName
	RemoteFile = gUPD_FileName
	prn('取得文件 ' + gUPD_FileName + ' 到本地目录 ' + LocalUpd + ' ...')
	FtpGetFile(LocalFile,RemoteFile,"bin")
	return 1
def FtpPutFile(Local,Remote,Mod):
	prn('	传输文件:' + Remote + ' ...')
	if Mod =="asc":
		#以只读二进制打开文件
		gFtpObj.storlines("STOR " + Remote, open(Local,'rb'))
	else:
		gFtpObj.storbinary("STOR " + Remote, open(Local,'rb'))	
	return 1
def FtpPutFiles(Local,Remote):
	prn('删除服务器['+gHost +'] '+ Remote + '目录')
	CmdText = "rm -rf " + Remote + "\n"
	gTelnetObj.write(CmdText)
	gTelnetObj.read_until(gCmdTip)
		
	#创建目录
	prn('创建服务器['+gHost +'] '+ Remote + '目录')
	gFtpObj.mkd(Remote)
	#转到$Home/xdlupd的目录下
	gFtpObj.cwd(Remote)
	prn('上传以下文件到['+gHost +'] '+ Remote + '目录下...')
	for ZipFileName in gArcFileListZip:		
		#以二进制传输
		FtpPutFile(Local + "\\" + ZipFileName,ZipFileName,"bin")
		
	LocalRun = gLocalTempPath + "\\" + gRUN_DIRNAME + "\\"
	LocalTmp = gLocalTempPath + "\\" + gTMP_DIRNAME + "\\"
	#把这两个文件放到Tmp目录下,以便上传到服务器	
	distutils.file_util.copy_file(LocalRun + "install_upd.sh",LocalTmp)
	distutils.file_util.copy_file(LocalRun + "version.ini",LocalTmp)
	
	#把这两个文件文本传输到Remote目录下
	FtpPutFile(Local + "\\install_upd.sh","install_upd.sh","asc")
	FtpPutFile(Local + "\\version.ini" ,"version.ini","asc")
	
	#转到上一层目录也就是$Home的目录下
	prn('上传以下文件到['+gHost +'] Home 目录下...')
	gFtpObj.cwd('..')	
	FtpPutFile("MakeBIN.sh" ,"MakeBIN.sh","asc")
	prn('文件上传完毕.')
	return 1

def ZipFile(FileName,ZipName):	
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
	zip = zipfile.ZipFile(ZipName,'w',zipfile.ZIP_DEFLATED)
	ZipObj(CurrentSrc,zip)
	zip.close()
	os.chdir(OldWorDir)
	return 1
def ZipObj(FileName,zip):
	''' 在调用这个函数之前,首先需要调用os.chdir()
		这个函数来改变当前的工作目录,
		在调用完成以后需要把工作目录设置回原来的
	'''
	if os.path.isdir(FileName):			
		#对每一个文件目录进行循环
		for fileitem in os.listdir(FileName):
			CurFilePath = FileName + '\\' + fileitem
			if os.path.isdir(CurFilePath):	
				ZipObj(CurFilePath,zip)
			else:
				print ('	添加文件 ==> ' + fileitem)
				zip.write(CurFilePath)
	else:
		zip.write(FileName)
	
	return 1
def CreateDir(Local):
	LocalRun = Local + "\\" + gRUN_DIRNAME + "\\"
	LocalSrc = Local + "\\" + gSRC_DIRNAME + "\\"
	LocalUpd = Local + "\\" + gUPD_DIRNAME + "\\"
	LocalTmp = Local + "\\" + gTMP_DIRNAME + "\\"
	
	if not os.path.exists(LocalRun):
		prn('创建目录:' + LocalRun)
		os.makedirs(LocalRun)
	if not os.path.exists(LocalSrc):
		prn('创建目录:' + LocalSrc)
		os.makedirs(LocalSrc)
	if not os.path.exists(LocalUpd):
		prn('创建目录:' + LocalUpd)
		os.makedirs(LocalUpd)
	if not os.path.exists(LocalTmp):
		prn('创建目录:' + LocalUpd)
		os.makedirs(LocalTmp)
	return 1
def ExecPBOBJFile():
	'''
	该函数事项生成app_smap.srj和autoupdate.srj这两个对象的语法文件
	app_smap.srj:是SMAP的工程文件
	autoupdate.srj:是升级的工程文件
	然后把app_smap.srj:这个文件导入到smap.pbl
	把autoupdate.srj:这个文件导入到autoupdate.pbl
	'''
	LocalRun = gLocalTempPath + "\\" + gRUN_DIRNAME + "\\"
	app_smap = LocalRun + "\\" + "app_smap.srj"
	#开始写app_smap.srj文件
	f_app_smap = open(app_smap,'w')
	tmpstr = '$PBExportHeader$app_smap.srj' + '\n'
	f_app_smap.writelines(tmpstr)
	tmpstr  = 'EXE:'
	tmpstr += LocalRun  + "smapexec.exe,"
	tmpstr += LocalRun  + "smap.pbr,0,1" + '\n'
	f_app_smap.writelines(tmpstr)
	
	#配置信息
	tmpstr  = 'CMP:0,0,0,2,0,0' + '\n'	
	#公司信息
	tmpstr  += 'COM:Huawei Technologies Co., Ltd.' + '\n'
	#描述信息
	tmpstr  += 'DES:Huawei smapexec.exe file' + '\n'
	#授权信息
	tmpstr  += 'CPY:Copyright(C) 1995-2008 Huawei Technologies Co., Ltd.' + '\n'	
	#产品名称信息
	tmpstr  += 'PRD:UIN PPS(C+G)' + '\n'	
	#版本信息
	tmpstr  += 'VER:' + gProjVerPrefix + '0' + '\n'
	f_app_smap.writelines(tmpstr)
	
	#PBD文件列表
	tmpstr  = 'PBD:' + LocalRun + "smap.pbl,,1"     + '\n'	
	tmpstr += 'PBD:' + LocalRun + "system.pbl,,1"   + '\n'
	tmpstr += 'PBD:' + LocalRun + "eppc.pbl,,1"     + '\n'	
	tmpstr += 'PBD:' + LocalRun + "eppc_a.pbl,,1"   + '\n'	
	tmpstr += 'PBD:' + LocalRun + "eppc_b.pbl,,1"   + '\n'	
	tmpstr += 'PBD:' + LocalRun + "eppc_c.pbl,,1"   + '\n'	
	tmpstr += 'PBD:' + LocalRun + "public.pbl,,1"   + '\n'
	tmpstr += 'PBD:' + LocalRun + "public_dddw.pbl,,1" + '\n'
	tmpstr += 'PBD:' + LocalRun + "public_g.pbl,,1" + '\n'
	tmpstr += 'PBD:' + LocalRun + "public_p.pbl,,1" + '\n'
	f_app_smap.writelines(tmpstr)	
	#关闭文件
	f_app_smap.close()
	
	#开始写autoupdate.srj文件
	app_Update = LocalRun  + "autoupdate.srj"
	f_app_Update = open(app_Update,'w')
	tmpstr = '$PBExportHeader$autoupdate.srj' + '\n'
	f_app_Update.writelines(tmpstr)
	tmpstr  = 'EXE:'
	tmpstr += LocalRun + "smap.exe,,0,1"
	f_app_Update.writelines(tmpstr)
	
	#配置信息
	tmpstr  = 'CMP:0,0,0,2,0,0' + '\n'	
	#公司信息
	tmpstr  += 'COM:Huawei Technologies Co., Ltd.' + '\n'
	#描述信息
	tmpstr  += 'DES:Huawei smap.exe file' + '\n'
	#授权信息
	tmpstr  += 'CPY:Copyright(C) 1995-2008 Huawei Technologies Co., Ltd.' + '\n'	
	#产品名称信息
	tmpstr  += 'PRD:UIN PPS(C+G)' + '\n'	
	#版本信息
	tmpstr  += 'VER:' + gProjVerPrefix + '0' + '\n'
	f_app_Update.writelines(tmpstr)
	
	#PBD文件列表
	tmpstr  = 'PBD:' + LocalRun + "autoupdate.pbl,,1"     + '\n'
	f_app_Update.writelines(tmpstr)
	#关闭文件
	f_app_Update.close()
			
	return 1
def ExecZip():
	LocalRun = gLocalTempPath + "\\" + gRUN_DIRNAME + "\\"
	LocalSrc = gLocalTempPath + "\\" + gSRC_DIRNAME + "\\"
	LocalTmp = gLocalTempPath + "\\" + gTMP_DIRNAME + "\\"
	LocalUpd = gLocalTempPath + "\\" + gUPD_DIRNAME + "\\"
	
	Count = len(gArcFileListOri)
	#按照列表进行压缩
	for i in range(0,Count):
		prn('压缩文件 ' + gArcFileListOri[i] + '==> ' + gArcFileListZip[i])
		ZipFile(LocalRun + gArcFileListOri[i],LocalTmp + gArcFileListZip[i])
		
	#RUN的压缩包
	prn('生成RUN包 : ' + gRUN_FileName)
	ZipFile(LocalRun ,LocalUpd + gRUN_FileName)
	
	#SRC的压缩包
	prn('生成SRC包 : ' + gSRC_FileName)
	ZipFile(LocalSrc ,LocalUpd + gSRC_FileName)
	
	return 1
def ExecPBCompile():
	LocalRun = gLocalTempPath + "\\" + gRUN_DIRNAME + "\\"
	LocalSrc = gLocalTempPath + "\\" + gSRC_DIRNAME + "\\"
	LocalTmp = gLocalTempPath + "\\" + gTMP_DIRNAME + "\\"
	#把这两以下文件放到RUN目录下,以便编译
	prn('拷贝pborcaw\ImportAppOBJ.orc文件到 ' + LocalRun + '目录.')
	distutils.file_util.copy_file("pborcaw\ImportAppOBJ.orc",LocalRun)
	prn('拷贝' + gPB_WorkSpace_Name + '文件到 ' + LocalRun + '目录.')
	distutils.file_util.copy_file(gPB_WorkSpace_Name,LocalRun)
	prn('拷贝app_smap.pbt文件到 ' + LocalRun + '目录.')
	distutils.file_util.copy_file("app_smap.pbt",LocalRun)
	prn('拷贝autoupdate.pbt文件到 ' + LocalRun + '目录.')
	distutils.file_util.copy_file("autoupdate.pbt",LocalRun)
	
	prn('按照以下命令格式执行导入*.sr*文件的操作:')
	#把生成后的两个文件导入到PBL中
	#通过执行以下命令
	OldWorDir = os.getcwd()
	#设置当前工作目录
	os.chdir(LocalRun)
	tmpstr = OldWorDir + "\\pborcaw\\pborcaA.exe ImportAppOBJ.orc"
	prn("导入*.sr*文件 ")
	os.system(tmpstr)
	#工作路径还原回来
	os.chdir(OldWorDir)
	
	PBRun = gPB_RUN + gLocalTempPath + "\\" + gRUN_DIRNAME + "\\" + gPB_WorkSpace_Name
	prn('按照以下命令格式运行PowerBuilder8:')
	prn(PBRun)
	os.system(PBRun)
	
	#编译完成后,清理不需要的文件
	prn('删除' + LocalRun + ' 目录下的 *.scc 文件')
	DelCmd = "del " + LocalRun + "*.scc"
	os.system(DelCmd)
	prn('删除' + LocalSrc + ' 目录下的 *.scc 文件')
	DelCmd = "del " + LocalSrc + "*.scc"
	os.system(DelCmd)
	prn('删除' + LocalRun + ' 目录下的 *.pbl 文件')
	DelCmd = "del " + LocalRun + "*.pbl"
	os.system(DelCmd)
	prn('删除' + LocalRun + ' 目录下的 *.pbt 文件')
	DelCmd = "del " + LocalRun + "*.pbt"
	os.system(DelCmd)
	prn('删除' + LocalRun + ' 目录下的 *.pbw 文件')
	DelCmd = "del " + LocalRun + "*.pbw"
	os.system(DelCmd)
	
	prn('删除' + LocalRun + ' 目录下的 *.sr* 文件')
	DelCmd = "del " + LocalRun + "*.sr*"
	os.system(DelCmd)
	
	prn('删除' + LocalRun + ' 目录下的 *.orc 文件')
	DelCmd = "del " + LocalRun + "*.orc*"
	os.system(DelCmd)
	
	prn('删除' + LocalRun + ' 目录下的 Copyright.txt 文件')
	DelCmd = "del " + LocalRun + "Copyright.txt"
	os.system(DelCmd)
	return 1
def TelExecCmd():	
	
	#gRemotePath
	
	#执行删除命令
	CmdText = "rm *SMAP_UPD.BIN\n"
	gTelnetObj.write(CmdText)
	gTelnetObj.read_until(gCmdTip)
	
	#回到Home目录下
	gTelnetObj.write("cd \n")	
	#执行归档命令
	gTelnetObj.read_until(gCmdTip)
	
	cmdstr = "./makeinstall.sh " + gRemotePath + " install_upd.sh " + gUPD_FileName +" \n" 
	prn('执行打包命令:' + cmdstr)
	gTelnetObj.write(cmdstr)
	gTelnetObj.read_until(gCmdTip)	
	return 1
#初始化一些公用对象
def InitObj():
	
	#=============================VSS object===================================
	gVssDatabaseObj.Open(gVssPath,gVssUser,gVssPass)
	
	#=============================FTP object===================================
	
	#创建Telnet连接	
	#=============================Telnet object===================================
	#在Login:后输入
	gTelnetObj.read_until("ogin:")
	gTelnetObj.write(gTelUser + "\n")
	#在Password:后输入密码
	gTelnetObj.read_until("assword:")
	gTelnetObj.write(gTelPass + "\n")
	gTelnetObj.read_until(gCmdTip)
	
	#=============================return===================================
	return 1
#销毁一些公用对象
def Destroy():
	#退出Telnet	
	gTelnetObj.write("exit\n")
	#print gTelnetObj.read_all()
	
	gFtpObj.quit()
	gFtpObj.close()
	
	return 1
def WinMain():
	EPPCProjPath = "$/EPPCV300R003C04b09/Develop/01.CI/1.7 Code/SMS/OCS&IN EPPCV300R003C04B090/SMAP"
	BASEProjPath = "$/EPPCV300R003C04b09/Develop/01.CI/1.7 Code/SMS/OCS&IN EPPCV300R003C04B090/BASELINE/CIN_UBASE_SMAP_EN_V2.0D340/E_SMAPV1.2"
	InitObj()
	
	#在gLocalTempPath下创建归档目录
	CreateDir(gLocalTempPath)
	
	#把VSS库上的文件取到RUN,SRC目录下
	prn('取EPPC代码文件到 ' + gRUN_DIRNAME + ' 目录')
	VssGetFile(gLocalTempPath + "\\" + gRUN_DIRNAME ,EPPCProjPath)
	prn('取EPPC代码文件到 ' + gSRC_DIRNAME + ' 目录')
	VssGetFile(gLocalTempPath + "\\" + gSRC_DIRNAME ,EPPCProjPath)
	prn('取基线代码文件到 ' + gRUN_DIRNAME + ' 目录')
	VssGetFile(gLocalTempPath + "\\" + gRUN_DIRNAME ,BASEProjPath)
	prn('取基线代码文件到 ' + gSRC_DIRNAME + ' 目录')
	VssGetFile(gLocalTempPath + "\\" + gSRC_DIRNAME ,BASEProjPath)
	prn('VSS库上的文件Get完毕')
	
	#生成PB编译的两个对象的语法文件
	ExecPBOBJFile()
	
	#执行PB编译
	ExecPBCompile()
	
	#压缩所有文件
	ExecZip()
	
	#把压缩好的文件传输到服务器
	FtpPutFiles(gLocalTempPath + "\\" + gTMP_DIRNAME ,gRemotePath)
	
	#执行打包命令
	TelExecCmd()
	
	#包打好包的BIN文件取下来
	ExecFtpGetFile()
	
	#把文件放到归档库上
	ExecVssPutFile()
	
	Destroy()
	#执行操作系统的命令
	os.system('pause')	
	return 1
if __name__ == '__main__' :
	WinMain()
	