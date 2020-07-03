from cefpython3 import cefpython as cef
import tkinter as tk

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
        tk.Frame.__init__(self, master)
    
    def change_browser(self, url): 
            if not self.browser:
                window_info = cef.WindowInfo()
                rect = [0, 0, self.winfo_width(), self.winfo_height()]
                window_info.SetAsChild(self.get_window_handle(), rect)
                self.window_info = window_info
                self.browser = cef.CreateBrowserSync(self.window_info,
                                                    url=url)
                assert self.browser
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