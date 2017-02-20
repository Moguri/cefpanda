from __future__ import print_function

from cefpython3 import cefpython
from panda3d.core import *

import os
import sys
import atexit
import pprint


class CefClientHandler:
    browser = None
    texture = None

    def __init__(self, browser, texture):
        self.browser = browser
        self.texture = texture

    def OnPaint(self, **kwargs):
        browser = kwargs['browser']
        element_type = kwargs['element_type']
        paint_buffer = kwargs['paint_buffer']
        width = kwargs['width']
        height = kwargs['height']

        if width != self.texture.get_x_size() or height != self.texture.get_y_size():
            return

        if element_type == cefpython.PET_VIEW:
            self.texture.set_ram_image(paint_buffer.GetString(mode="bgra", origin="bottom-left"))
        else:
            raise Exception("Unknown element_type: %s" % element_type)

    def GetViewRect(self, **kwargs):
        browser = kwargs['browser']
        rect_out = kwargs['rect_out']
        rect_out.append(0)
        rect_out.append(0)
        rect_out.append(self.texture.get_x_size())
        rect_out.append(self.texture.get_y_size())
        return True

    def OnLoadError(self, **kwargs):
        print("Load Error")
        pprint.pprint(kwargs)


class CEFPanda(object):
    _UI_SCALE = 1.0

    def __init__(self):
        cefpython.Initialize({
            #"log_severity": cefpython.LOGSEVERITY_INFO,
            #"release_dcheck_enabled": False,  # Enable only when debugging
            # This directories must be set on Linux
            "locales_dir_path": cefpython.GetModuleDirectory()+"/locales",
            "resources_dir_path": cefpython.GetModuleDirectory(),
            "browser_subprocess_path": "%s/%s" % (
                cefpython.GetModuleDirectory(), "subprocess"),
        })
        self._cef_texture = Texture()
        self._cef_texture.set_compression(Texture.CMOff)
        self._cef_texture.set_component_type(Texture.TUnsignedByte)
        self._cef_texture.set_format(Texture.FRgba4)

        card_maker = CardMaker("browser2d")
        card_maker.set_frame(-self._UI_SCALE, self._UI_SCALE, -self._UI_SCALE, self._UI_SCALE)
        node = card_maker.generate()
        self._cef_node = render2d.attachNewNode(node)
        self._cef_node.set_texture(self._cef_texture)
        self._cef_node.set_transparency(TransparencyAttrib.MAlpha)

        winhnd = base.win.getWindowHandle().getIntHandle()
        wininfo = cefpython.WindowInfo()
        wininfo.SetAsOffscreen(winhnd)
        wininfo.SetTransparentPainting(True)

        self.browser = cefpython.CreateBrowserSync(
            wininfo,
            {},
            navigateUrl=''
        )
        self.browser.SetClientHandler(CefClientHandler(self.browser, self._cef_texture))

        self._is_loaded = False
        self._js_onload_queue = []
        self.browser.SetClientCallback("OnLoadEnd", self._load_end)


        self.jsbindings = cefpython.JavascriptBindings()
        self.browser.SetJavascriptBindings(self.jsbindings)
        self._js_func_queue = []

        self._set_browser_size()
        base.accept('window-event', self._set_browser_size)

        base.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        base.accept('keystroke', self._handle_key)

        base.taskMgr.add(self._cef_message_loop, "CefMessageLoop")

        def shutdown_cef():
            cefpython.Shutdown()

        atexit.register(shutdown_cef)

    def _load_end(self, *args, **kwargs):
        self._is_loaded = True

        # Register any functions
        for i in self._js_func_queue:
            self.set_js_function(*i)

        self._js_func_queue = []

        # Execute any queued javascript
        for i in self._js_onload_queue:
            self.execute_js(i)

        self._js_onload_queue = []

    # Due to an issue in CEFPython, a load_url() call needs to be made
    # before load_string() will work.
    # CEFPython issue: https://code.google.com/p/chromiumembedded/issues/detail?id=763
    def load_string(self, string, url):
        url = os.path.abspath(url)
        if sys.platform != 'win32':
            url = 'file://' + url
        self._is_loaded = False
        self.browser.GetMainFrame().LoadString(string, url)

    def load(self, url):
        if url:
            url = os.path.abspath(url)
            if sys.platform != 'win32':
                url = 'file://' + url
            self._is_loaded = False
            self.browser.GetMainFrame().LoadUrl(url)
        else:
            self.browser.GetMainFrame().LoadUrl('about:blank')

    def execute_js(self, js, onload=False):
        if onload and not self._is_loaded:
            self._js_onload_queue.append(js)
        else:
            self.browser.GetMainFrame().ExecuteJavascript(js)

    def set_js_function(self, name, func):
        if not self._is_loaded:
            self._js_func_queue.append((name, func))
        else:
            self.jsbindings.SetFunction(name, func)
            self.jsbindings.Rebind()

    def _set_browser_size(self, window=None):
        width = int(round(base.win.getXSize() * self._UI_SCALE))
        height = int(round(base.win.getYSize() * self._UI_SCALE))

        # We only want to resize if the window size actually changed.
        if self._cef_texture.get_x_size() != width and self._cef_texture.get_y_size() != height:
            self._cef_texture.set_x_size(width)
            self._cef_texture.set_y_size(height)

            # Clear the texture
            img = PNMImage(width, height)
            img.fill(0, 0, 0)
            img.alpha_fill(0)
            self._cef_texture.load(img)
            self.browser.WasResized()

    def _handle_key(self, keyname):
        keycode = ord(keyname)
        vkeys = {
            8: cefpython.VK_BACK,
            13: cefpython.VK_RETURN,
            27: cefpython.VK_ESCAPE,
        }

        keyevent = {
            "type": cefpython.KEYEVENT_RAWKEYDOWN,
        }

        if keycode in vkeys:
            keyevent['windows_key_code'] = vkeys[keycode]
        else:
            keyevent['character'] = keycode

        self.browser.SendKeyEvent(keyevent)

        keyevent['type'] = cefpython.KEYEVENT_KEYUP
        self.browser.SendKeyEvent(keyevent)

        keyevent['type'] = cefpython.KEYEVENT_CHAR
        self.browser.SendKeyEvent(keyevent)

    def _cef_message_loop(self, task):
        cefpython.MessageLoopWork()
        self.browser.SendFocusEvent(True)

        #if base.mouseWatcherNode.has_mouse():
        #    mouse = base.mouseWatcherNode.getMouse()
        #    rx, ry = mouse.get_x(), mouse.get_y()
        #    x = (rx + 1.0) / 2.0 * self._cef_texture.get_x_size()
        #    y = (ry + 1.0) / 2.0 * self._cef_texture.get_y_size()
        #    y = self._cef_texture.get_y_size() - y
        #    self.browser.SendMouseMoveEvent(x, y, mouseLeave=False)

        return task.cont
