import tkinter 
from tkinter.filedialog import asksaveasfile, askopenfile
from tkinter.messagebox import showerror, askyesno
from tkinter import ttk
from collections import deque
import atexit


#----------------------------------------------------------- class section

def quit():
    global root
    if mainForm.book.recent.last != -1:
        mainForm.book.recent.updateFile()
    mainForm.book.saveSwitch(mark = "for all")

    root.quit()

class TextBox(tkinter.Text):
    def __init__(self, place, width=400, height=200):
        
        tkinter.Text.__init__(self, place, width=400, height=200)
        
        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)

        if command in ("insert", "delete", "replace"):
            self.event_generate("<<TextModified>>")

        return result

class TabPage(ttk.Frame):
    def __init__(self, place, FILE_NAME = "New Document"):
        ttk.Frame.__init__(self,place)
        self.home = place
        place.add(self, text = FILE_NAME)
        place.hide(self)

    def addStar(self, name):
        self.home.add(self, text = name + "*")
        return True


class Document(object):
    def __init__(self, place, name):
        if name != tkinter.NONE:
            self.name = name
            self.dtab = TabPage(place, self.name.rpartition("/")[2])
            self.state = "Not New"
        else:
            self.state = "New Document"
            self.name = self.state
            self.dtab = TabPage(place)
        self.txt = TextBox(self.dtab)
        self.txt.pack()
        self.txt.bind("<<TextModified>>", self.onModification)
        self.flag = False

    def onModification(self, event):
        self.flag = self.dtab.addStar(self.name.rpartition("/")[2])

    def update(self, name):
        self.name = name
        m = self.dtab.master
        m.tab(self.dtab, text = self.name.rpartition("/")[2])
        self.state = "Not New"

class TabControl(ttk.Notebook):
    def __init__(self, master = None, **kw):
        ttk.Notebook.__init__(self, mainForm.mf)
        self.pages = {}
        self.num = 0
        self.addPage(tkinter.NONE)
    def addPage(self, FILE_NAME=tkinter.NONE):
        #tabPage = TabPage(self, FILE_NAME)
        #self.add(tabPage)
        #tabPage.doc = Document(tabPage)
        doc = Document(self, FILE_NAME)
        self.select(doc.dtab)
        
        self.pages.update({self.num : doc})
        self.num +=1
        pass
    def deletePage(self):
        ttab = self.currentTab()
        mainForm.book.saveSwitch()
        del self.pages[ttab].dtab
        del self.pages[ttab]
        self.forget(ttab)
        self.num -=1
    def currentTab(self):
        ttab = self.index(self.select())
        return ttab


class Book(TabControl):
    def __init__(self, *args):
        self.recent = RecentDocs()
        self.FILE_NAME = tkinter.NONE
    def open(self):
        inp = askopenfile(mode="r")
        if inp is None:
            return
        self.FILE_NAME = inp.name
        data = inp.read()
        tabControl.addPage(self.FILE_NAME)
        tabID = tabControl.num-1
        tabControl.pages[tabID].txt.delete('1.0', tkinter.END)
        tabControl.pages[tabID].txt.insert('1.0', data)
        tabControl.pages[tabID].flag = False
        tabControl.pages[tabID].update(self.FILE_NAME)
        self.recent.updateList(self.FILE_NAME)
        self.FILE_NAME = tkinter.NONE

    def saveSwitch(self, mark = "0"):
        if mark == "for all":
            for key in tabControl.pages:
                if tabControl.pages[key].flag == True:
                    saveStatus = askyesno("Есть несохраненные изменения","Сохранить внесенные в " + tabControl.pages[key].name + " изменения?")
                    if saveStatus == True:
                        mainForm.book.saveDoc()
                    else:
                        root.quit()
                        pass
        else:
            tabID = tabControl.currentTab()
            curr = tabControl.pages[tabID]
            if curr.flag == True:
                saveStatus = askyesno("Есть несохраненные изменения","Сохранить внесенные изменения?")
                if saveStatus == True:
                    mainForm.book.saveDoc()
                else:
                    root.quit()
        pass
    def saveDoc(self):
        tabID = tabControl.currentTab()
        curr = tabControl.pages[tabID]
        if curr.state == "New Document":
            self.saveDocAs()
        else:
            data = curr.txt.get('1.0',tkinter.END)
            self.FILE_NAME = curr.name
            out = open(self.FILE_NAME, 'w')
            out.write(data)
            out.close()
            self.recent.updateList(self.FILE_NAME)
            curr.update(self.FILE_NAME)
            self.FILE_NAME = tkinter.NONE
    def saveDocAs(self):
        tabID = tabControl.currentTab()
        curr = tabControl.pages[tabID]
        out = asksaveasfile(mode='w', defaultextension='.txt')
        data = curr.txt.get('1.0',tkinter.END)
        try:
            out.write(data.rstrip())
        except Exception:
            showerror(title="Oops!", message="Unable to save file....")
        try:
            self.FILE_NAME = out.name
            self.recent.updateList(self.FILE_NAME)
            curr.update(self.FILE_NAME)
        except AttributeError:
            self.FILE_NAME = tkinter.NONE
        finally:
            self.FILE_NAME = tkinter.NONE
    def closeDoc(self):
        self.saveDoc()
        tabControl.deletePage()
    def newDoc(self):
        tabControl.addPage(tkinter.NONE)

        pass


class MemorizingDict(dict):
    def __init__(self):
        self._history = deque(maxlen=10)
    def set(self, key, value):
        self._history.append(key)
        self[key] = value
    def getHistory(self):
        return self._history
    pass


class RecentDocs(Book):
    #__dict__ = {"recentList" : []}
    def __init__(self):
        self.last = -1
        try:
            rec = open("RecentDocs.txt", "r+")
            self.recentList = MemorizingDict()
            for (i,line) in enumerate(rec):
                if line!="\n":
                    self.recentList.set(i,line)
                    self.last = i
                pass
            rec.close()
        except OSError:
            rec = open("RecentDocs.txt", "w+")
            rec.close()
        finally:
            mainForm.menu.setRecentList(self.recentList)
            pass
            
    def selectItem(self,key):
        FILE_NAME = self.recentList[key]
        value = open(FILE_NAME)

        data = value.read()
        tabControl.addPage(value)
        self.tabID = tabControl.num-1
        tabControl.pages[self.tabID].doc.doc.delete('1.0', tkinter.END)
        tabControl.pages[self.tabID].doc.doc.insert('1.0', data)
        tabControl.tab(self.tabID, text = FILE_NAME)
        pass
    def updateList(self,value):
        self.recentList.set(self.last+1,value)
        self.last = len(self.recentList)-1
        mainForm.menu.setRecentList(self.recentList)
        pass
    def updateFile(self):
        rec = open("RecentDocs.txt", "w")
        spisok = []
        for key in self.recentList:
            spisok.append(self.recentList[key])
            pass
        rec.write("\n".join(spisok))
        rec.close()
        pass
pass


class MainMenu(tkinter.Menu):
    def __init__(self):
        self.mb = tkinter.Menu(mainForm.mf)
        mainForm.mf.config(menu=self.mb)
        self.fileMenu = tkinter.Menu(self.mb)
        
        self.fileMenu.add_command(label="Open", command= lambda: mainForm.book.open())
        self.fileMenu.add_command(label="Close", command= lambda: mainForm.book.closeDoc())
        self.fileMenu.add_command(label="New Document", command= lambda: mainForm.book.newDoc())
        self.fileMenu.add_command(label="Save", command= lambda: mainForm.book.saveDoc())
        self.fileMenu.add_command(label="Save As", command= lambda: mainForm.book.saveDocAs())
        self.fileMenu.add_command(label="Exit", command= lambda: quit())
        self.mb.add_cascade(label="File", menu=self.fileMenu)
        self.recentMenu = tkinter.Menu(self.fileMenu)
        self.rID = {}
        spisok = []
        for i in range(10):
            self.recentMenu.add_command(label="No Recent File")
            
            self.rID.update({i:self.recentMenu.index(tkinter.END)})
            pass
        spisok = self.recentMenu.children.values()
        self.fileMenu.add_cascade(label="Recent Documents", menu=self.recentMenu)
        self.tabsMenu = tkinter.Menu(self.mb)
        self.mb.add_cascade(label="Tabs", menu=self.tabsMenu)
        self.tabsMenu.add_command(label="Add Tab", command=tabControl.addPage)
        self.tabsMenu.add_command(label="Delete Tab", command=tabControl.deletePage)
        
        

    def setRecentList(self, recentList):
        for (key) in recentList:
            self.recentMenu.entryconfig(index=key+1,label=recentList[key], command= lambda: mainForm.book.recent.selectItem(key))
            pass
        pass

class MainForm(object):
    def __init__(self):
        self.mf = tkinter.Toplevel()

    def createBook(self):
        self.book = Book()
        pass

    def createMenu(self):
        self.menu = MainMenu()
       
        
#--------------------------------------------------------------- class section end


if __name__ == "__main__":
    root = tkinter.Tk()
    root.title("TextEditor")
    root.withdraw()

    mainForm = MainForm()
    mainForm.mf.minsize(width=400, height=400)
    mainForm.mf.maxsize(width=600, height=600)

    tabControl = TabControl()
    mainForm.createMenu()
    mainForm.createBook()
    tabControl.pack()

    mainForm.mf.protocol('WM_DELETE_WINDOW', quit)

    root.mainloop()





