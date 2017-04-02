import sys
sys.path.append('../../')

import cefpanda
from direct.showbase.ShowBase import ShowBase, DirectObject
import panda3d.core as p3d


p3d.load_prc_file_data('', 'win-size 1280 720')


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.win.set_close_request_event('escape')
        self.accept('escape', sys.exit)

        # Setup ui
        self.ui = cefpanda.CEFPanda()
        self.ui.load('ui/main.html')


app = Game()
app.run()
