import os
import sys
import tkinter as tk
import pandas as pd

# Simple implementation of Observer Design Pattern
class Observable:
    def __init__(self):
        self.observers = []
    def add_observers(self, observer):
        self.observers.append(observer)
    def notify_observers(self):
        for observer in self.observers:
            observer.notify(self)
            
class Observer:
    def __init__(self, observable):
        observable.add_observers(self)
        
    def notify(self, observable):
        print("Notified from ", observable)

def center(win):
    windowWidth = win.winfo_reqwidth()
    windowHeight = win.winfo_reqheight()            
    positionRight = int(win.winfo_screenwidth()/2 - windowWidth/2)
    positionDown = int(win.winfo_screenheight()/2 - windowHeight/2)
    win.geometry("+{}+{}".format(positionRight, positionDown))

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

    
class AnalyzerTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
    
class AnalyzerData(Observable):
    def __init__(self, loadedData, gui, root, level, name):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        self.level = level
        self.name = name
        self.gui = gui
        self.root = root
        # Watch for updates in loaded data
        loadedData.add_observers(self)
    