class ParserState(object):
    def __init__(self, context):
        self._context = context

    def handle_line(self, line):
        raise NotImplemented

    def enter(self):
        pass

    def exit(self):
        pass

class StateManager(dict):
    def __init__(self):
        self._line_number = 0
        self._current_line = None
        self._previous_line = None
        self._states = {}

    def _register_state(self, state):
        self._states[state.name] = state

    def _get_state(self, name):
        return self._states[name]

    def change_state(self, name):
        self._current_state.exit()
        self._previous_state= self._current_state
        self._current_state = self._get_state(name)
        self._current_state.enter()

    @property
    def previous_state(self):
        return self._previous_state.name

    def handle_line(self, line):
        self._line_number += 1
        self._current_line = line
        self._current_state.handle_line(line)
        self._previous_line = line

    @property
    def current_line(self):
        return self._current_line

    @property
    def previous_line(self):
        return self._previous_line

    @property
    def line_number(self):
        return self._line_number

    @property
    def current_state(self):
        return self._current_state

class BaseParser(StateManager):
    def __init__(self, infile):
        super(BaseParser, self).__init__()
        self.infile = infile
        self.results = []

    def parse(self):
        for line in self.infile:
            clean_line = line.strip() 
            self.handle_line(clean_line)
