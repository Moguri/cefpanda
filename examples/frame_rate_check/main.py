import sys

from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d

import cefpanda


p3d.load_prc_file_data(
    '',
    'win-size 1280 720\n'
    'show-frame-rate-meter 1\n'
)


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.accept('escape', sys.exit)

        # Setup ui
        self.ui = cefpanda.CEFPanda()
        self.ui.load_url('https://frames-per-second.appspot.com/')


if __name__ == '__main__':
    APP = Game()
    APP.run()
