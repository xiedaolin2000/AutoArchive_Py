# -*- coding: gb2312 -*-
#==========================================================================
#			SMAP�Զ��鵵Python�ű�
#����:
#	�ù���ʵ����,���ļ���ָ����VSS��ȡ�ļ�����,��PB���߱���,������ɺ�
#	��ָ�����ļ�����Ҫ�����ѹ��,��ѹ������ļ��ϴ���Unix�������Ͻ��д��,����һ��������
#	�����ɺ��������ȡ����.
#
#����:	л����
#����:	2008-07-28
#��ʷ:
#	
#==========================================================================
import getpass
import sys
import os
import socket
import telnetlib	#Ϊ��ʹ��Telnet����
import ftplib		#����FTP����
import zipfile 		#����ѹ������
import distutils.file_util	#ʹ��һЩ�ļ�������������
#����win32com�� SourceSafe.0
import win32com.client

def DebugInfo():
	return 1
def prn(str):
	'''
	��ӡ��ʾ��Ϣ
	'''
	print(str)
	return 1

gVssPath = r"\\192.168.1.4\eppcv300r003c04b090\SourceSafe.ini"
gVssUser = "xiedaolin"
gVssPass = "xiedaolin"

#�鵵���ϸ�������ŵ�·��
#�ַ���ǰ���һ����ĸr��ʾ���Բ�ʹ��ת���ַ�.
gVssPath_Archive = r"\\192.168.1.4\PowerBuilder_VSS\SourceSafe.ini"
gArcPath_MDD = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/1.MDD"
gArcPath_RUN = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/2.RUN"
gArcPath_SRC = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/3.SRC"
gArcPath_UPD = "$/EPPCV300R003C04B081/SoftWare/3.SMAP/4.UPD"


gHost = "192.168.1.5"	#������IP��ַ
gCmdTip="/smapupd>"	#�ڲ�ͬ�Ļ�����,������ʾ����һ��.
#���ݲ�ͬ��ƽ̨���ò�ͬ��������ʾ����
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
gTelUser = "smapupd"	#��½���û���
gTelPass = "qwer][po"	#��½������

gPB_RUN = r'"d:\program files\Sybase\PowerBuilder 8.0\pb80.exe " /w  '
gPB_WorkSpace_Name = "SMAP_RUN_Archive.pbw"
#�����İ汾�Ÿ�ʽ EPPCV***R***C**B**N (N = 1,2,3,...)
gProjVerPrefix  = "EPPCV300R003C04B09"
gProjVersuffix  = "2"	#��ʾ���汾�ڼ���
gProjVersion    = gProjVerPrefix + gProjVersuffix
gUPD_FileName   = "CIN_" + gProjVersion + "_SMAP_UPD.BIN"
gRUN_FileName   = "CIN_" + gProjVersion + "_SMAP_RUN.zip"
gSRC_FileName   = "CIN_" + gProjVersion + "_SMAP_SRC.zip"

gLocalTempPath = r"d:\temp\TMP_" + gProjVersion
gUPD_DIRNAME    = "UPD"
gRUN_DIRNAME    = "RUN"
gSRC_DIRNAME    = "SRC"
gTMP_DIRNAME    = "TMP"

#���صĹ鵵ȫ·��
gLocalPath_RUN = gLocalTempPath + "\\" + gRUN_DIRNAME
gLocalPath_SRC = gLocalTempPath + "\\" + gSRC_DIRNAME
gLocalPath_UPD = gLocalTempPath + "\\" + gUPD_DIRNAME
gLocalPath_TMP = gLocalTempPath + "\\" + gTMP_DIRNAME



gRemotePath = "xdlupd"	#�鵵���������ϵ�·��

#ѹ�����ļ�����ѹ������ļ�����Ӧ��ϵ
gArcFileListOri = ["smidll.dll","cygwin1.dll","encode.dll","SmapDll.dll","ConvertToUni.dll","gzip.exe","smapexec.exe","servicecfg.cfg","system.pbd","smap.pbd","public.pbd","public_p.pbd","public_g.pbd","public_dddw.pbd","eppc.pbd","up.bmp","down.bmp","hwhelp.dat","hweppchelp.dat","PPC_SMAP_HELP.chm","base_smap_help.chm","huawei.bmp",    "huawei.ico",   "WordMapping.dat","eppc_a.pbd","eppc_b.pbd","eppc_c.pbd"]
gArcFileListZip = ["smidll.zip","cygwin1.zip","encode.zip","SmapDll.zip","ConvertToUni.zip","gzip.zip","smapexec.zip","servicecfg.zip","system.zip","smap.zip","public.zip","public_p.zip","public_g.zip","public_dddw.zip","eppc.zip","up.zip","down.zip","hwhelp.zip","hweppchelp.zip","PPC_SMAP_HELP.zip","base_smap_help.zip","huaweibmp.zip","huaweiico.zip","WordMapping.zip","eppc_a.zip","eppc_b.zip","eppc_c.zip"]

#=============================================================================================================================================================

#һ�����Ժ����VSSDatabase COM����
prn('��ʼ��COM����... ����VSS����')
gVssDatabaseObj = win32com.client.Dispatch("SourceSafe")

prn('����FTP�������� ...')
gFtpObj = ftplib.FTP(gHost,gTelUser,gTelPass)

prn('����Telnet�������� ...')
gTelnetObj = telnetlib.Telnet(gHost)


def VssGetFile(LocalPath,Vss_path):
	VssItem = gVssDatabaseObj.VSSItem(Vss_path)
	for item in VssItem.GetItems():
		#����Ǹ������ļ���
		if item.Type == 0:
			prn(u"����VSSĿ¼==>" + "/" +  item.Name)
			VssGetFile(LocalPath + u"\\"+ item.Name,Vss_path + "/" +  item.Name)			
		else:	#���ļ�
			prn(u"ȡ���ļ�==>" + item.Name)
			#VSSFLAG_KEEPYES  ���ļ��ǿ�д״̬
			item.Get(LocalPath + u"\\"+ item.Name,1)
	return 1
def ExecVssPutFile():
	prn('�Ƿ���Ҫ�ѹ鵵���Զ��ŵ��鵵����.')
	prn('ע��:')
	prn('1.Ҫ��ȷ���ù鵵���·��.' )
	prn('2.���õ�·���б����ǿ�Ŀ¼,������ʧ��.')
	inputstr = raw_input("�Ƿ����?[Y/N,Y--��,����--��]:")
	inputstr = inputstr.upper()	
	if inputstr != "Y":
		return 0
	
	#��Ҫ��������һ��COM����,ʹ��ԭ���Ļ�������.
	ArchiveVSS_DB_OBJ = win32com.client.Dispatch("SourceSafe")
	ArchiveVSS_DB_OBJ.Open(gVssPath_Archive,gVssUser,gVssPass)
	
	LocalUpd = gLocalTempPath + "\\" + gUPD_DIRNAME + "\\"
	#��RUN���ŵ�VSS����
	prn('�� ' + gRUN_FileName + '�ļ�,�ϴ���VSS��,·��' + gArcPath_RUN)
	prn('gArcPath_RUN = ' + gArcPath_RUN)
	VssProject = ArchiveVSS_DB_OBJ.VSSItem(gArcPath_RUN)
	VssProject.Add(LocalUpd + gRUN_FileName , 'Xiedaolin',0)
	
	#��SRC���ŵ�VSS����
	prn('�� ' + gSRC_FileName + '�ļ�,�ϴ���VSS��,·��' + gArcPath_SRC)
	VssProject = ArchiveVSS_DB_OBJ.VSSItem(gArcPath_SRC)
	VssProject.Add(LocalUpd + gSRC_FileName , 'Xiedaolin',0)
	
	#��UPD���ŵ�VSS����
	prn('�� ' + gUPD_FileName + '�ļ�,�ϴ���VSS��,·��' + gArcPath_UPD)
	VssProject = ArchiveVSS_DB_OBJ.VSSItem(gArcPath_UPD)
	VssProject.Add(LocalUpd + gUPD_FileName , 'Xiedaolin',0)
	return 1
def FtpGetFile(Local,Remote,Mod):	
	if Mod =="asc":
		# wb==>��ֻ�������ƴ��ļ�
		gFtpObj.retrlines('RETR ' + Remote, open(Local, 'wb').write)
	else:
		gFtpObj.retrbinary('RETR ' + Remote, open(Local, 'wb').write)
	return 1
def ExecFtpGetFile():
	LocalUpd   = gLocalTempPath + "\\" + gUPD_DIRNAME + "\\"
	LocalFile  = LocalUpd + gUPD_FileName
	RemoteFile = gUPD_FileName
	prn('ȡ���ļ� ' + gUPD_FileName + ' ������Ŀ¼ ' + LocalUpd + ' ...')
	FtpGetFile(LocalFile,RemoteFile,"bin")
	return 1
def FtpPutFile(Local,Remote,Mod):
	prn('	�����ļ�:' + Remote + ' ...')
	if Mod =="asc":
		#��ֻ�������ƴ��ļ�
		gFtpObj.storlines("STOR " + Remote, open(Local,'rb'))
	else:
		gFtpObj.storbinary("STOR " + Remote, open(Local,'rb'))	
	return 1
def FtpPutFiles(Local,Remote):
	prn('ɾ��������['+gHost +'] '+ Remote + 'Ŀ¼')
	CmdText = "rm -rf " + Remote + "\n"
	gTelnetObj.write(CmdText)
	gTelnetObj.read_until(gCmdTip)
		
	#����Ŀ¼
	prn('����������['+gHost +'] '+ Remote + 'Ŀ¼')
	gFtpObj.mkd(Remote)
	#ת��$Home/xdlupd��Ŀ¼��
	gFtpObj.cwd(Remote)
	prn('�ϴ������ļ���['+gHost +'] '+ Remote + 'Ŀ¼��...')
	for ZipFileName in gArcFileListZip:		
		#�Զ����ƴ���
		FtpPutFile(Local + "\\" + ZipFileName,ZipFileName,"bin")
		
	LocalRun = gLocalTempPath + "\\" + gRUN_DIRNAME + "\\"
	LocalTmp = gLocalTempPath + "\\" + gTMP_DIRNAME + "\\"
	#���������ļ��ŵ�TmpĿ¼��,�Ա��ϴ���������	
	distutils.file_util.copy_file(LocalRun + "install_upd.sh",LocalTmp)
	distutils.file_util.copy_file(LocalRun + "version.ini",LocalTmp)
	
	#���������ļ��ı����䵽RemoteĿ¼��
	FtpPutFile(Local + "\\install_upd.sh","install_upd.sh","asc")
	FtpPutFile(Local + "\\version.ini" ,"version.ini","asc")
	
	#ת����һ��Ŀ¼Ҳ����$Home��Ŀ¼��
	prn('�ϴ������ļ���['+gHost +'] Home Ŀ¼��...')
	gFtpObj.cwd('..')	
	FtpPutFile("MakeBIN.sh" ,"MakeBIN.sh","asc")
	prn('�ļ��ϴ����.')
	return 1

def ZipFile(FileName,ZipName):	
	absPath = os.path.abspath(FileName)
	WorkDir = ''
	#�õ�������·�������ļ�����Ŀ¼��
	CurrentSrc = os.path.split(absPath)[1]
	
	if os.path.isdir(absPath):
		WorkDir = absPath
		CurrentSrc = '.\\'
	else:
		WorkDir = os.path.dirname(absPath)
	
	OldWorDir = os.getcwd()
	#���õ�ǰ����Ŀ¼
	os.chdir(WorkDir)
	#����һ��ѹ����
	zip = zipfile.ZipFile(ZipName,'w',zipfile.ZIP_DEFLATED)
	ZipObj(CurrentSrc,zip)
	zip.close()
	os.chdir(OldWorDir)
	return 1
def ZipObj(FileName,zip):
	''' �ڵ����������֮ǰ,������Ҫ����os.chdir()
		����������ı䵱ǰ�Ĺ���Ŀ¼,
		�ڵ�������Ժ���Ҫ�ѹ���Ŀ¼���û�ԭ����
	'''
	if os.path.isdir(FileName):			
		#��ÿһ���ļ�Ŀ¼����ѭ��
		for fileitem in os.listdir(FileName):
			CurFilePath = FileName + '\\' + fileitem
			if os.path.isdir(CurFilePath):	
				ZipObj(CurFilePath,zip)
			else:
				print ('	����ļ� ==> ' + fileitem)
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
		prn('����Ŀ¼:' + LocalRun)
		os.makedirs(LocalRun)
	if not os.path.exists(LocalSrc):
		prn('����Ŀ¼:' + LocalSrc)
		os.makedirs(LocalSrc)
	if not os.path.exists(LocalUpd):
		prn('����Ŀ¼:' + LocalUpd)
		os.makedirs(LocalUpd)
	if not os.path.exists(LocalTmp):
		prn('����Ŀ¼:' + LocalUpd)
		os.makedirs(LocalTmp)
	return 1
def ExecPBOBJFile():
	'''
	�ú�����������app_smap.srj��autoupdate.srj������������﷨�ļ�
	app_smap.srj:��SMAP�Ĺ����ļ�
	autoupdate.srj:�������Ĺ����ļ�
	Ȼ���app_smap.srj:����ļ����뵽smap.pbl
	��autoupdate.srj:����ļ����뵽autoupdate.pbl
	'''
	LocalRun = gLocalTempPath + "\\" + gRUN_DIRNAME + "\\"
	app_smap = LocalRun + "\\" + "app_smap.srj"
	#��ʼдapp_smap.srj�ļ�
	f_app_smap = open(app_smap,'w')
	tmpstr = '$PBExportHeader$app_smap.srj' + '\n'
	f_app_smap.writelines(tmpstr)
	tmpstr  = 'EXE:'
	tmpstr += LocalRun  + "smapexec.exe,"
	tmpstr += LocalRun  + "smap.pbr,0,1" + '\n'
	f_app_smap.writelines(tmpstr)
	
	#������Ϣ
	tmpstr  = 'CMP:0,0,0,2,0,0' + '\n'	
	#��˾��Ϣ
	tmpstr  += 'COM:Huawei Technologies Co., Ltd.' + '\n'
	#������Ϣ
	tmpstr  += 'DES:Huawei smapexec.exe file' + '\n'
	#��Ȩ��Ϣ
	tmpstr  += 'CPY:Copyright(C) 1995-2008 Huawei Technologies Co., Ltd.' + '\n'	
	#��Ʒ������Ϣ
	tmpstr  += 'PRD:UIN PPS(C+G)' + '\n'	
	#�汾��Ϣ
	tmpstr  += 'VER:' + gProjVerPrefix + '0' + '\n'
	f_app_smap.writelines(tmpstr)
	
	#PBD�ļ��б�
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
	#�ر��ļ�
	f_app_smap.close()
	
	#��ʼдautoupdate.srj�ļ�
	app_Update = LocalRun  + "autoupdate.srj"
	f_app_Update = open(app_Update,'w')
	tmpstr = '$PBExportHeader$autoupdate.srj' + '\n'
	f_app_Update.writelines(tmpstr)
	tmpstr  = 'EXE:'
	tmpstr += LocalRun + "smap.exe,,0,1"
	f_app_Update.writelines(tmpstr)
	
	#������Ϣ
	tmpstr  = 'CMP:0,0,0,2,0,0' + '\n'	
	#��˾��Ϣ
	tmpstr  += 'COM:Huawei Technologies Co., Ltd.' + '\n'
	#������Ϣ
	tmpstr  += 'DES:Huawei smap.exe file' + '\n'
	#��Ȩ��Ϣ
	tmpstr  += 'CPY:Copyright(C) 1995-2008 Huawei Technologies Co., Ltd.' + '\n'	
	#��Ʒ������Ϣ
	tmpstr  += 'PRD:UIN PPS(C+G)' + '\n'	
	#�汾��Ϣ
	tmpstr  += 'VER:' + gProjVerPrefix + '0' + '\n'
	f_app_Update.writelines(tmpstr)
	
	#PBD�ļ��б�
	tmpstr  = 'PBD:' + LocalRun + "autoupdate.pbl,,1"     + '\n'
	f_app_Update.writelines(tmpstr)
	#�ر��ļ�
	f_app_Update.close()
			
	return 1
def ExecZip():
	LocalRun = gLocalTempPath + "\\" + gRUN_DIRNAME + "\\"
	LocalSrc = gLocalTempPath + "\\" + gSRC_DIRNAME + "\\"
	LocalTmp = gLocalTempPath + "\\" + gTMP_DIRNAME + "\\"
	LocalUpd = gLocalTempPath + "\\" + gUPD_DIRNAME + "\\"
	
	Count = len(gArcFileListOri)
	#�����б����ѹ��
	for i in range(0,Count):
		prn('ѹ���ļ� ' + gArcFileListOri[i] + '==> ' + gArcFileListZip[i])
		ZipFile(LocalRun + gArcFileListOri[i],LocalTmp + gArcFileListZip[i])
		
	#RUN��ѹ����
	prn('����RUN�� : ' + gRUN_FileName)
	ZipFile(LocalRun ,LocalUpd + gRUN_FileName)
	
	#SRC��ѹ����
	prn('����SRC�� : ' + gSRC_FileName)
	ZipFile(LocalSrc ,LocalUpd + gSRC_FileName)
	
	return 1
def ExecPBCompile():
	LocalRun = gLocalTempPath + "\\" + gRUN_DIRNAME + "\\"
	LocalSrc = gLocalTempPath + "\\" + gSRC_DIRNAME + "\\"
	LocalTmp = gLocalTempPath + "\\" + gTMP_DIRNAME + "\\"
	#�����������ļ��ŵ�RUNĿ¼��,�Ա����
	prn('����pborcaw\ImportAppOBJ.orc�ļ��� ' + LocalRun + 'Ŀ¼.')
	distutils.file_util.copy_file("pborcaw\ImportAppOBJ.orc",LocalRun)
	prn('����' + gPB_WorkSpace_Name + '�ļ��� ' + LocalRun + 'Ŀ¼.')
	distutils.file_util.copy_file(gPB_WorkSpace_Name,LocalRun)
	prn('����app_smap.pbt�ļ��� ' + LocalRun + 'Ŀ¼.')
	distutils.file_util.copy_file("app_smap.pbt",LocalRun)
	prn('����autoupdate.pbt�ļ��� ' + LocalRun + 'Ŀ¼.')
	distutils.file_util.copy_file("autoupdate.pbt",LocalRun)
	
	prn('�������������ʽִ�е���*.sr*�ļ��Ĳ���:')
	#�����ɺ�������ļ����뵽PBL��
	#ͨ��ִ����������
	OldWorDir = os.getcwd()
	#���õ�ǰ����Ŀ¼
	os.chdir(LocalRun)
	tmpstr = OldWorDir + "\\pborcaw\\pborcaA.exe ImportAppOBJ.orc"
	prn("����*.sr*�ļ� ")
	os.system(tmpstr)
	#����·����ԭ����
	os.chdir(OldWorDir)
	
	PBRun = gPB_RUN + gLocalTempPath + "\\" + gRUN_DIRNAME + "\\" + gPB_WorkSpace_Name
	prn('�������������ʽ����PowerBuilder8:')
	prn(PBRun)
	os.system(PBRun)
	
	#������ɺ�,������Ҫ���ļ�
	prn('ɾ��' + LocalRun + ' Ŀ¼�µ� *.scc �ļ�')
	DelCmd = "del " + LocalRun + "*.scc"
	os.system(DelCmd)
	prn('ɾ��' + LocalSrc + ' Ŀ¼�µ� *.scc �ļ�')
	DelCmd = "del " + LocalSrc + "*.scc"
	os.system(DelCmd)
	prn('ɾ��' + LocalRun + ' Ŀ¼�µ� *.pbl �ļ�')
	DelCmd = "del " + LocalRun + "*.pbl"
	os.system(DelCmd)
	prn('ɾ��' + LocalRun + ' Ŀ¼�µ� *.pbt �ļ�')
	DelCmd = "del " + LocalRun + "*.pbt"
	os.system(DelCmd)
	prn('ɾ��' + LocalRun + ' Ŀ¼�µ� *.pbw �ļ�')
	DelCmd = "del " + LocalRun + "*.pbw"
	os.system(DelCmd)
	
	prn('ɾ��' + LocalRun + ' Ŀ¼�µ� *.sr* �ļ�')
	DelCmd = "del " + LocalRun + "*.sr*"
	os.system(DelCmd)
	
	prn('ɾ��' + LocalRun + ' Ŀ¼�µ� *.orc �ļ�')
	DelCmd = "del " + LocalRun + "*.orc*"
	os.system(DelCmd)
	
	prn('ɾ��' + LocalRun + ' Ŀ¼�µ� Copyright.txt �ļ�')
	DelCmd = "del " + LocalRun + "Copyright.txt"
	os.system(DelCmd)
	return 1
def TelExecCmd():	
	
	#gRemotePath
	
	#ִ��ɾ������
	CmdText = "rm *SMAP_UPD.BIN\n"
	gTelnetObj.write(CmdText)
	gTelnetObj.read_until(gCmdTip)
	
	#�ص�HomeĿ¼��
	gTelnetObj.write("cd \n")	
	#ִ�й鵵����
	gTelnetObj.read_until(gCmdTip)
	
	cmdstr = "./makeinstall.sh " + gRemotePath + " install_upd.sh " + gUPD_FileName +" \n" 
	prn('ִ�д������:' + cmdstr)
	gTelnetObj.write(cmdstr)
	gTelnetObj.read_until(gCmdTip)	
	return 1
#��ʼ��һЩ���ö���
def InitObj():
	
	#=============================VSS object===================================
	gVssDatabaseObj.Open(gVssPath,gVssUser,gVssPass)
	
	#=============================FTP object===================================
	
	#����Telnet����	
	#=============================Telnet object===================================
	#��Login:������
	gTelnetObj.read_until("ogin:")
	gTelnetObj.write(gTelUser + "\n")
	#��Password:����������
	gTelnetObj.read_until("assword:")
	gTelnetObj.write(gTelPass + "\n")
	gTelnetObj.read_until(gCmdTip)
	
	#=============================return===================================
	return 1
#����һЩ���ö���
def Destroy():
	#�˳�Telnet	
	gTelnetObj.write("exit\n")
	#print gTelnetObj.read_all()
	
	gFtpObj.quit()
	gFtpObj.close()
	
	return 1
def WinMain():
	EPPCProjPath = "$/EPPCV300R003C04b09/Develop/01.CI/1.7 Code/SMS/OCS&IN EPPCV300R003C04B090/SMAP"
	BASEProjPath = "$/EPPCV300R003C04b09/Develop/01.CI/1.7 Code/SMS/OCS&IN EPPCV300R003C04B090/BASELINE/CIN_UBASE_SMAP_EN_V2.0D340/E_SMAPV1.2"
	InitObj()
	
	#��gLocalTempPath�´����鵵Ŀ¼
	CreateDir(gLocalTempPath)
	
	#��VSS���ϵ��ļ�ȡ��RUN,SRCĿ¼��
	prn('ȡEPPC�����ļ��� ' + gRUN_DIRNAME + ' Ŀ¼')
	VssGetFile(gLocalTempPath + "\\" + gRUN_DIRNAME ,EPPCProjPath)
	prn('ȡEPPC�����ļ��� ' + gSRC_DIRNAME + ' Ŀ¼')
	VssGetFile(gLocalTempPath + "\\" + gSRC_DIRNAME ,EPPCProjPath)
	prn('ȡ���ߴ����ļ��� ' + gRUN_DIRNAME + ' Ŀ¼')
	VssGetFile(gLocalTempPath + "\\" + gRUN_DIRNAME ,BASEProjPath)
	prn('ȡ���ߴ����ļ��� ' + gSRC_DIRNAME + ' Ŀ¼')
	VssGetFile(gLocalTempPath + "\\" + gSRC_DIRNAME ,BASEProjPath)
	prn('VSS���ϵ��ļ�Get���')
	
	#����PB���������������﷨�ļ�
	ExecPBOBJFile()
	
	#ִ��PB����
	ExecPBCompile()
	
	#ѹ�������ļ�
	ExecZip()
	
	#��ѹ���õ��ļ����䵽������
	FtpPutFiles(gLocalTempPath + "\\" + gTMP_DIRNAME ,gRemotePath)
	
	#ִ�д������
	TelExecCmd()
	
	#����ð���BIN�ļ�ȡ����
	ExecFtpGetFile()
	
	#���ļ��ŵ��鵵����
	ExecVssPutFile()
	
	Destroy()
	#ִ�в���ϵͳ������
	os.system('pause')	
	return 1
if __name__ == '__main__' :
	WinMain()
	