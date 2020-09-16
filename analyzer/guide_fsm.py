import tkinter as tk
import enum

#from transitions import Machine
from transitions.extensions import GraphMachine as Machine
from abc import ABC, abstractmethod


class StateImpl(ABC):
    @abstractmethod
    def action(self, context):
        pass

class InitStateImpl (StateImpl):
    def action(self, context):
        print("In Init state")

class AStartStateImpl (StateImpl):
    def action(self, context):
        print("In AStart state")

class AEndStateImpl (StateImpl):
    def action(self, context):
        print("In AEnd state")

class BStateImpl (StateImpl):
    def action(self, context):
        print("In B state")

class EndStateImpl (StateImpl):
    def action(self, context):
        print("In End state")


class SidoStateImpl (StateImpl):
    def action(self, context):
        print("In Sido state")


class SidoDetailsStateImpl (StateImpl):
    def action(self, context):
        print("In Sido Details state")

class HopelessStateImpl (StateImpl):
    def action(self, context):
        print("In Hopeles state")


class HopelessDetailsStateImpl (StateImpl):
    def action(self, context):
        print("In Hopeless Details state")

class BoostStateImpl (StateImpl):
    def action(self, context):
        print("In Boost state")


class BoostDetailsStateImpl (StateImpl):
    def action(self, context):
        print("In Boost Details state")

class States(enum.Enum):
    INIT = InitStateImpl()
    Astart = AStartStateImpl()
    Aend = AEndStateImpl()
    B = BStateImpl()
    End = EndStateImpl()
    A1 = SidoStateImpl()
    A2 = HopelessStateImpl()
    A3 = BoostStateImpl()
    A11 = SidoDetailsStateImpl()
    A21 = HopelessDetailsStateImpl()
    A31 = BoostDetailsStateImpl()

    def __init__(self, impl):
        self.impl = impl

    def action(self, context):
        self.impl.action(context)

transitions = [['proceed', States.INIT, States.Astart],
               ['proceed', States.Astart, States.Aend],
               ['proceed', States.Aend, States.B],
               ['proceed', States.B, States.End],
               ['details', States.Astart, States.A1],
               ['proceed', States.A1, States.A2],
               ['proceed', States.A2, States.A3],
               ['proceed', States.A3, States.Aend],
               ['details', States.A1, States.A11],
               ['proceed', States.A11, States.A1],
               ['details', States.A2, States.A21],
               ['proceed', States.A21, States.A2],
               ['details', States.A3, States.A31],
               ['proceed', States.A31, States.A3]]

# Guide engine as a finite state machine
# Uses transitions package to implement the finite machine taking care of state transition
# and then use State design pattern to handle different behaviour of different states

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

class FiniteStateMachine(Observable):
    def __init__(self):
        super().__init__()
        # Below after_state_change call back could make it another method to call notify_observers and invoke action methods in states as well.
        m = Machine(self, states=States, transitions=transitions, initial=States.INIT, use_pygraphviz=False, after_state_change=self.notify_observers)
        self.fsm = m
        self.file = 'c:/users/cwong29/AppData/Local/Temp/my_state_diagram1.png'
        self.dump_graph()
 #       assert self.is_INIT()
 #       assert self.state is States.INIT
 #       state = m.get_state(States.INIT)  # get transitions.State object
 #       print(state.name)  # >>> INIT
 #       self.proceed()
 #       self.proceed()
 #       assert self.is_Aend()

    def dump_graph(self):
        self.fsm.get_graph().draw(self.file, prog='dot')


class Gui(tk.Frame):
    def __init__(self, parent, fsm):
        tk.Frame.__init__(self, parent, width=1500, height=500)
        self.pack()
        self.fsm = fsm
        self.fsm.add_observers(self)
        self.canvas = tk.Canvas(self, width=1500, height=500)
        self.canvas.pack(side=tk.BOTTOM)
        self.img = tk.PhotoImage(file=fsm.file)
        self.canvas.create_image(750, 250, image=self.img)

        bottomframe = tk.Frame(self)
        bottomframe.pack(side=tk.BOTTOM)

        proceedButton = tk.Button(bottomframe, text="Proceed", command=self.fsm.proceed)
        proceedButton.pack(side=tk.LEFT)
        detailsButton = tk.Button(bottomframe, text="Details", command=self.fsm.details)
        detailsButton.pack(side=tk.LEFT)
        
    def notify(self, observable):
        self.fsm.dump_graph()
        print("changed")
        self.img = tk.PhotoImage(file=self.fsm.file)
        self.canvas.create_image(750, 250, image=self.img)




if __name__ == '__main__':
    fsm = FiniteStateMachine()

    root = tk.Tk()
    gui = Gui(root, fsm)
    root.mainloop()
