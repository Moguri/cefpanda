import sys

from direct.showbase.ShowBase import ShowBase

import cefpanda


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.accept('escape', sys.exit)

        # Setup ui
        self.ui = cefpanda.CEFPanda()
        def call_py1():
            print('Python called (func1)')
        self.ui.set_js_function('call_py1', call_py1)
        def call_py2():
            print('Python called (func2)')
        self.ui.set_js_function('call_py2', call_py2)
        self.ui.load_file('ui/main.html')


if __name__ == '__main__':
    APP = Game()
    APP.run()
