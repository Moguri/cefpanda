import sys

from direct.showbase.ShowBase import ShowBase

import cefpanda


class App(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.accept('escape', sys.exit)

        # Setup ui
        self.ui = cefpanda.CEFPanda(
            transparent=False,
            size=[-0.75, 0.75, -0.75, 0.75],
            # parent=base.aspect2d,
        )
        self.ui.node().set_scale(0.9)
        self.ui.node().set_pos(0.05, 0.0, -0.1)
        self.ui.set_js_function('call_py', self.handler_js_to_py)
        self.ui.load_file('ui/main.html')

    def handler_js_to_py(self, color):
        print("Python handler called with '{}'".format(color))
        self.ui.exec_js_func('color_text', color)


if __name__ == '__main__':
    APP = App()
    APP.run()
