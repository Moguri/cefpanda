import json
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
        self.ui.set_js_function('update_options', self.update_options)
        self.ui.load('ui/main.html')
        self.ui.execute_js('ui_update_options({})'.format(self.get_options()), onload=True)

    def get_options(self):
        wp = self.win.get_properties()
        disp_info = self.pipe.get_display_information()
        options = json.dumps({
            'selected_resolution': '{} x {}'.format(wp.get_x_size(), wp.get_y_size()),
            'resolutions': sorted(list({
                '{} x {}'.format(disp_info.get_display_mode_width(i), disp_info.get_display_mode_height(i))
                for i in range(disp_info.get_total_display_modes())
            }), key=lambda x: int(x.split(' x ')[1])),
            'fullscreen': wp.get_fullscreen(),
        })

        return options


    def update_options(self, options):
        wp = p3d.WindowProperties()
        resx, resy = [int(i) for i in options['selected_resolution'].split(' x ')]
        wp.set_size(resx, resy)
        wp.set_fullscreen(options['fullscreen'])
        self.win.request_properties(wp)


app = Game()
app.run()
