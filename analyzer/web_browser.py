from cefpython3 import cefpython as cef
import tkinter as tk
import platform
import ctypes

# Platforms
WINDOWS = (platform.system() == "Windows")
LINUX = (platform.system() == "Linux")
MAC = (platform.system() == "Darwin")

class MainFrame(tk.Frame):

    def __init__(self, root):
        # MainFrame
        tk.Frame.__init__(self, root)

        # BrowserFrame
        self.browser_frame = BrowserFrame(self)
        # self.browser_frame.grid(row=1, column=1,
        #                         sticky=(tk.N + tk.S + tk.E + tk.W))
        # tk.Grid.rowconfigure(self, 1, weight=1)
        # tk.Grid.columnconfigure(self, 1, weight=1)
        self.browser_frame.pack(fill=tk.BOTH, expand=True)

        # Pack MainFrame
        self.pack(fill=tk.BOTH, expand=tk.YES)

class BrowserFrame(tk.Frame):

    def __init__(self, master):
        self.closing = False
        self.browser = None
        self.window_info = None
        self.url = ''
        tk.Frame.__init__(self, master)
        self.bind("<Configure>", self.on_configure)
    
    def refresh(self):
        self.browser.Reload()

    def change_browser(self, url): 
        self.url = url
        if not self.browser:
            window_info = cef.WindowInfo()
            rect = [0, 0, self.winfo_width(), self.winfo_height()]
            window_info.SetAsChild(self.get_window_handle(), rect)
            self.window_info = window_info
            self.browser = cef.CreateBrowserSync(self.window_info, url=url)
            assert self.browser
            self.browser.SetClientHandler(LifespanHandler(self))
            self.message_loop_work()
        else:
            self.browser.LoadUrl(url)

    def get_window_handle(self):
        if self.winfo_id() > 0:
            return self.winfo_id()

    def message_loop_work(self):
        cef.MessageLoopWork()
        self.after(100, self.message_loop_work)

    def close(self):
        self.browser = None
        self.destroy()

    def on_configure(self, event):
        width = event.width
        height = event.height
        self.on_mainframe_configure(width, height)

    def on_root_configure(self):
        # Root <Configure> event will be called when top window is moved
        if self.browser:
            self.browser.NotifyMoveOrResizeStarted()

    def on_mainframe_configure(self, width, height):
        if self.browser:
            if WINDOWS:
                ctypes.windll.user32.SetWindowPos(
                    self.browser.GetWindowHandle(), 0,
                    0, 0, width, height, 0x0002)
            elif LINUX:
                self.browser.SetBounds(0, 0, width, height)
            self.browser.NotifyMoveOrResizeStarted()

class LifespanHandler(object):

    def __init__(self, tkFrame):
        self.tkFrame = tkFrame
    
    def OnBeforePopup(self, browser, **_):
        if _['target_url'].startswith(self.tkFrame.url):
            print("URL: " + self.tkFrame.url + " is loading the popup")
            self.tkFrame.browser.LoadUrl(_['target_url'])
            return True
        print("URL: " + self.tkFrame.url + " is not loading the popup")
        return False