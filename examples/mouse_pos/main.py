import sys

from direct.showbase.ShowBase import ShowBase

import cefpanda


class App(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.accept('escape', sys.exit)

        # Setup ui
        self.ui = cefpanda.CEFPanda(transparent=False)
        self.ui.load_file('ui/main.html')


if __name__ == '__main__':
    APP = App()
    APP.run()
