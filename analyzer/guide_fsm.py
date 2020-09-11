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


if __name__ == '__main__':
    m = Machine(states=States, transitions=transitions, initial=States.INIT, use_pygraphviz=False)
    assert m.is_INIT()
    assert m.state is States.INIT
    state = m.get_state(States.INIT)  # get transitions.State object
    print(state.name)  # >>> INIT
    m.proceed()
    m.proceed()
    assert m.is_Aend()