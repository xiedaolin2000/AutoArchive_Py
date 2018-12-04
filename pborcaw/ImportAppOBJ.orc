# script for compiling pb project with pborca.exe tool
# all parameters should be separated by comma
# to specify comma itself use meta symbol %
# example: build executable exeName, iconName, pbrName


#the command to start orca session for PB version 80
session begin pborc80.dll


#the list could be separated by ; like in PB library list
set liblist begin
smap.pbl  ,1
eppc.pbl ,1
eppc_a.pbl ,1
eppc_b.pbl ,1
eppc_c.pbl ,1
public.pbl ,1
public_dddw.pbl ,1
public_g.pbl ,1
public_p.pbl ,1
system.pbl ,1
autoupdate.pbl
set liblist end

#sets current application
set application smap.pbl,app_smap
#set application smap.pbl

#导入一个对象
import app_smap.srj,smap.pbl
import autoupdate.srj,autoupdate.pbl

#executes system command
#eg: sys <system command>

#Displays text messages
#echo 导入对象完毕

#displays current date and time
timestamp

#ends orca session
session end


