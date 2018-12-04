# script for compiling pb project with pborca.exe tool
# all parameters should be separated by comma
# to specify comma itself use meta symbol %
# example: build executable exeName, iconName, pbrName


#the command to start orca session for PB version 80
session begin pborc80.dll


#entryName or/and entryType could be * for all objects
#entryType: app, dw, fn, menu, query, struct, uo, pipe, proxy, or win.
#copy item pblSrc, entryName, entryType, pblDst

#creates a new library with comments
#library create pblName, comments

#the list could be separated by ; like in PB library list
set liblist begin
#here also could be some comments
#to include PBL into exe - specify 0 after coma
smap.pbl;  ,0
#you can cpesify a resource file for PBL (PBL should be compiled to PBD/DLL)
smap.pbl;  ,1
eppc.pbl; ,1
eppc_a.pbl; ,1
eppc_b.pbl; ,1
eppc_c.pbl; ,1
public.pbl; ,1
public_dddw.pbl; ,1
public_g.pbl; ,1
public_p.pbl; ,1
system.pbl; ,1
set liblist end

#sets current application
set application smap.pbl, app_smap

#rebuild application full, incremental, or migrate
build app full

#creates executable
#eg:  build exe exeName, iconName, pbrName, <pcode | machinecode>
build exe smapexec.exe, huawei.ico, smap.pbr, pcode

#deletes object
#eg: delete item pblName, entryName, entryType


#deletes objects from deleteFromLib that found in primaryLib
#eg: delete duplex primaryLib, deleteFromLib


#executes system command
#eg: sys <system command>

#Displays text messages
echo text

#displays current date and time
timestamp

#ends orca session
session end


