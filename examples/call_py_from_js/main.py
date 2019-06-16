import math
import sys

from direct.showbase.ShowBase import ShowBase

import cefpanda


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.accept('escape', sys.exit)

        self.ui = cefpanda.CEFPanda()
        self.ui.set_js_function('change_color', self.change_color)
        self.ui.load('main.html')

        self.cube = self.loader.loadModel('box.egg.pz')
        self.cube.reparentTo(self.render)

        self.taskMgr.add(self.spin_camera_task, 'spin_camera_task')

    def change_color(self, color):
        if color == 'white':
            code = [255, 255, 255]

        elif color == 'red':
            code = [255, 0, 0]

        elif color == 'green':
            code = [0, 255, 0]

        elif color == 'blue':
            code = [0, 0, 255]

        else:
            raise TypeError('Invalid color supplied')

        self.cube.setColor(*code, 255)

    def spin_camera_task(self, task):
        angle_degrees = task.time * 30
        angle_radians = angle_degrees * (math.pi / 180.0)
        self.camera.setPos(10 * math.sin(angle_radians), -10 * math.cos(angle_radians), 5)
        self.camera.lookAt(self.cube)
        return task.cont


if __name__ == '__main__':
    APP = Game()
    APP.run()
