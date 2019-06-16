import json
import sys

from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d

import cefpanda

p3d.load_prc_file_data('', 'win-size 1280 720')


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.accept('escape', sys.exit)

        # Setup ui
        self.ui = cefpanda.CEFPanda()
        self.ui.set_js_function('update_options', self.update_options)
        self.ui.load('ui/main.html')
        options = json.dumps(self.get_options())
        self.ui.execute_js(f'ui_update_options({options})', onload=True)

    def get_options(self):
        winprops = self.win.get_properties()
        disp_info = self.pipe.get_display_information()
        options = {
            'selected_resolution': '{} x {}'.format(winprops.get_x_size(), winprops.get_y_size()),
            'resolutions': sorted(list({
                '{} x {}'.format(
                    disp_info.get_display_mode_width(i),
                    disp_info.get_display_mode_height(i)
                )
                for i in range(disp_info.get_total_display_modes())
            }), key=lambda x: -int(x.split(' x ')[1])),
            'fullscreen': winprops.get_fullscreen(),
        }

        return options


    def update_options(self, options):
        winprops = p3d.WindowProperties()
        resx, resy = [int(i) for i in options['selected_resolution'].split(' x ')]
        winprops.set_size(resx, resy)
        winprops.set_fullscreen(options['fullscreen'])
        self.win.request_properties(winprops)


if __name__ == '__main__':
    APP = Game()
    APP.run()
