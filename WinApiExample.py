#Copyright (c) 2007, Alexander Semenyuk
#All rights reserved.
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from Tkinter import *
from win32gui import *
from win32con import *
import win32process
import win32api
import os
from PIL import Image, ImageTk, PngImagePlugin, IcoImagePlugin,ImageGrab
import StringIO, binascii
import subprocess
import sys
import time
#TODO: Fix all the numerous hacks, WM_PRINT + PAINT, port to WX? , Custom Config

#*************VARS*****************
act=os.getcwd()
WINUM=0
HWND=None
HEIGHT=win32api.GetSystemMetrics (1)
WIDTH= win32api.GetSystemMetrics(0)/2
ICON_HEADER = binascii.unhexlify('00 00 01 00 01 00 20 20 00 00 00 00 00 00 A8 08 00 00 16 00 00 00'.replace(' ', ''))
os.chdir(os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))) #IF INSIDE EXE
global count
count=0
BG_COLOR='black'
BTN_BORDER='orange'
DOCK_SIZE='58'
B_SZ=int(DOCK_SIZE)-10
T_HEIGHT=HEIGHT-int(DOCK_SIZE)
ICON_DEFAULT='default.png' #get a small 48x48 png for this, needed for misbehaving apps like no$gba
TRANSPARENT=0.8
list1=[]

ShowWindow(FindWindow("Shell_TrayWnd", None), SW_HIDE)

#*********SETTINGS CONFIG***********
if os.path.exists(act+"\conf.txt"):
	f=open(act+'\conf.txt','r')
	#BG_COLOR=f.readline().strip('\r\n')
	#BTN_BORDER=f.readline().strip('\r\n')
	#DOCK_SIZE=f.readline().strip('\r\n')
	#B_SZ=int(DOCK_SIZE)-10
	#ICON_DEFAULT=f.readline().strip('\r\n')
	TRANSPARENT=float(f.readline().strip('\r\n'))
	list1 = f.readlines()
	f.close()
	

#*****WINDOW PREVIEWS****** Would be better to use Sendmessage + WM_PRINT (this is hack) 
class tooltip(object):
	def __init__(self,widget):
		self.button=widget
		self.tool=None
		self.x=self.y=0
	def show(self):
		if(self.button.pict!=None):
			self.text=GetWindowText(self.button.getpid())
			if self.tool or not self.text:
				return
			x,y,cx,cy = self.button.bbox("insert")
			x = x + self.button.winfo_rootx() - 32#Better to use screen - dock_height
			y = y + cy + self.button.winfo_rooty() - 140  #used to be 32 and before that ...27?
			self.tool = Toplevel(self.button,bg='black')
			self.tool.wm_overrideredirect(1)
			self.tool.wm_attributes("-topmost", 1,"-alpha",.98)
			self.tool.wm_geometry("+%d+%d" % (x, y))
			##ffffe0
			
			pic=self.button.pict
			labe = Label(self.tool,bg='black',image=pic)
			labe.image=pic
			#*********THE OLD TOOLTIPS***********
			#else:
			#	pic=ImageTk.PhotoImage(self.button.ir.resize((24,24)))
			#label = Label(self.tool, text=self.text, justify=LEFT,bg="black", fg="white",relief=SOLID, borderwidth=1)#,font=("Comic Sans", "8", "bold"))
			#	labe = Label(self.tool,bg='black',image=pic)
			#	labe.image=pic
			#label.pack(side=TOP)
			
			labe.pack(ipadx=1)
		
		
	def hide(self):
		toolT=self.tool
		self.tool = None
		if toolT:
			toolT.destroy()

def create(widget):
	toolTip = tooltip(widget)
	def enter(event):
		toolTip.show()
	def leave(event):
		toolTip.hide()
	widget.bind('<Enter>', enter)
	widget.bind('<Leave>', leave)

def getico(loc):
	#Better way?
	try:
		b=win32api.LoadLibraryEx (loc, 0, LOAD_LIBRARY_AS_DATAFILE)
		for e in win32api.EnumResourceNames (b, RT_ICON):
			data = win32api.LoadResource(b, RT_ICON, e)
			stream = StringIO.StringIO(ICON_HEADER + data)
			ir=Image.open(stream)
			if(ir.getextrema()[1] > 200):
				if(ir.size[-1] > B_SZ-10): #32
					break
	except:
		ir =Image.open(ICON_DEFAULT)
	return ir

class btn(Button):
	def __init__(self,root,Name,Pid,NUM):
		self.id=NUM
		self.name=Name
		self.pid=Pid
		self.pict=None
		self.han = win32process.GetWindowThreadProcessId(self.pid)[1] 
		self.handle = win32api.OpenProcess(PROCESS_ALL_ACCESS,False, self.han)
		self.path = win32process.GetModuleFileNameEx(self.handle, 0)
		#print self.path
		
		v= (self.path.rpartition('\\') [2]).split('.')[ 0]#could cause bugs if EXE is misnamed before execution (unlikely)

		self.ir=getico(self.path)
		
		self.ir=self.ir.resize((B_SZ,B_SZ))
		self.image1 = ImageTk.PhotoImage(self.ir)
			
		Button.__init__(self,root,width=B_SZ, relief=RIDGE,activebackground=BTN_BORDER, bg='black',highlightbackground='yellow', command=NONE)
		
		
		self.config(image=self.image1,command=self.action)
		self.po = Menu(self, tearoff=0)
		self.po.add_command(label='Minimize',command=lambda x=self.pid : ShowWindow(x,SW_MINIMIZE))
		self.po.add_command(label='Maximize',command=lambda x=self.pid : ShowWindow(x,SW_MAXIMIZE))
		self.po.add_command(label='Restore',command=lambda x=self.pid : ShowWindow(x,4) and SetForegroundWindow(self.pid))
		self.po.add_command(label='Close',command=self.close)
		self.bind("<Button-3>", self.menu)
		create(self)
		self.update()
	def action(self):
		Button.flash(self)
		if(IsIconic(self.pid)):
			ShowWindow(self.pid,4)
			SetForegroundWindow(self.pid)
			time.sleep(0.1) 
			self.grab()
		elif(self.pid==HWND):
			self.grab()
			time.sleep(0.1) 
			ShowWindow(self.pid,SW_MINIMIZE)
		else:
			ShowWindow(self.pid,5)
			SetForegroundWindow(self.pid)
			time.sleep(0.1) 
			self.grab()
	def update(self):
		if (GetForegroundWindow()==self.pid):
			self.grab()
		self.after(500, self.update)
	def menu(self,x):
		self.po.tk_popup(x.x_root, x.y_root)
	def getpid(self):
		return self.pid
	def close(self):
			SetForegroundWindow(self.pid)
			PostMessage(self.pid,WM_CLOSE, 0, 0)
	def grab(self):
		bbox =GetWindowRect(self.pid)
		self.pict = ImageTk.PhotoImage(ImageGrab.grab(bbox).resize((158,126), Image.ANTIALIAS))
	
class dockframe(Frame):

	def windowEnumerationHandler(self,hwnd, resultList):
		if IsWindowVisible(hwnd):
			val = GetWindowLong(hwnd,GWL_STYLE)
			txt = GetWindowText(hwnd)
			if GetParent(hwnd)==0: 
				if (GetWindow(hwnd,GW_OWNER)==0 or GetWindow(hwnd,GW_OWNER)==GetDesktopWindow()):
					if (val & WS_EX_CONTROLPARENT) or (val & WS_EX_TOOLWINDOW) or (val & WS_MINIMIZEBOX):
						resultList.append((hwnd, txt))

        def update(self):
                windows = [] #must be list
		hans=set([])
                i=1
                EnumWindows(self.windowEnumerationHandler, windows)
		index=len(windows)-1 #TOTAL NUMBER OF WINDOWS OPEN
                for w in windows: #w[1] is window title
			hans.add(windows[index][0])
			hans.add(windows[0][0])
			
                        if(i>self.wincount):
				loc=0
				j=index
				j=index
				c=len(self.handles)
				self.handles.add(windows[index][0])
				while (c == len(self.handles) and j>0):
					j-=1
					self.handles.add(windows[j][0])
                                b = btn(self,windows[index][1],windows[j][0],1)
                                b.pack(side=RIGHT, padx=2, pady=2)
                                self.wins.append(b) # list of buttons
                                self.wincount+=1
			index-=1
                        i+=1
                
                if(len(windows)<len(self.wins)):
			c=self.handles - hans
			W=len(self.wins)-1
			while(W!=-1):
				if(list(c).count(self.wins[W].pid)!=0):
					self.wins.pop(W).destroy()
					self.wincount-=1
				W-=1
			
		handles=hans
                global WINUM
                WINUM=self.wincount
		self.update
                self.after(100, self.update)
        def __init__(self,n,color):
                Frame.__init__(self,n,bg=color,relief=GROOVE,bd=5)
                self.wincount=0
                self.wins=[]
		self.handles=set([])
                return
                

class rubber(Tk):
        def __init__(self):
                Tk.__init__(self)
        def update(self):
		if(GetWindowText(GetForegroundWindow())!='nul'):
			global HWND
			HWND=GetForegroundWindow()
                global WINUM 
		si=int(DOCK_SIZE)
                self.geometry('%dx%d+%d+%d'%((si*(WINUM+count)+8),si+8,(WIDTH-(((WINUM+count)*si)/2)),(HEIGHT-si)))  
                self.after(100, self.update)

def exit():
	f=open(act+"\conf.txt",'w')
	f.write(str(TRANSPARENT)+'\n')
	for item in list1:
		f.write(item.rstrip('\r\n')+"\n")#yea ..wtf
	f.close()
	ShowWindow(FindWindow("Shell_TrayWnd", None), 4)
	root.destroy()	
def addl():
	import tkFileDialog
	k=tkFileDialog.askopenfilename(title="Select Executable", filetypes=[('EXE Files','*.exe')], parent=dock)
	if k!="" and k!=None:
		list1.append(k)
		addlaunch(k)
	
root = rubber()
root.overrideredirect(1)

po = Menu(root, tearoff=0)
po.add_separator()
po.add_command(label='Add Launcher',command=addl)
po.add_command(label='Show Taskbar',command=lambda x="Shell_TrayWnd": ShowWindow(FindWindow(x, None), 4))
po.add_command(label='Hide Taskbar',command=lambda x="Shell_TrayWnd": ShowWindow(FindWindow(x, None), SW_HIDE))
po.add_command(label='Exit',command=exit)
po.add_separator()
def popup(event):
	po.tk_popup(event.x_root, event.y_root)

dock = dockframe(root,BG_COLOR)
dock.bind("<Button-3>", popup)
def pop(x):
	subprocess.Popen(x)
def addlaunch(loc):
	global count
	ir=getico(loc)
	ir=ir.resize((B_SZ,B_SZ))
	global li
	li.append(ImageTk.PhotoImage(ir))
	b1 = Button(dock, width=B_SZ, relief=FLAT,activebackground='black', bg=BG_COLOR,fg='white', image=li[count], command=lambda x=loc: pop(x))
	b1.pack(side=LEFT, anchor=W, padx=2, pady=2)
	b1.bind("<Button-3>", popup)
	count+=1
	
global li
li=[]
cmd=[]

if(len(list1)!=0):
	for n in list1:
		cmd.append((n.strip('\r\n')))   
		addlaunch(n.strip('\r\n'))
		
	
root.resizable(0,0)
root.wm_attributes("-topmost", 1,"-alpha",TRANSPARENT)
myH= int(eval(root.wm_frame()))
root.title('nul')
dock.pack(side=TOP, fill=X)
dock.update()
root.update()
mainloop()


#=============================================================
#eg2:

import win32api
lib_hnd = win32api.LoadLibrary( "user32.dll" )
if lib_hnd:
fn_addr = win32api.GetProcAddress( lib_hnd, "MessageBeep" ) # returns int(2010532466)
if fn_addr:
# Here I'd like to call fn_addr. In C it would be plain fn_addr()
win32api.FreeLibrary( lib_hnd )