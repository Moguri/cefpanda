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
        self.popup_img = PNMImage(0, 0)
        self.popup_pos = [0, 0]
        self.popup_show = False

    def OnPopupShow(self, **kwargs):
        self.popup_show = kwargs['show']

    def OnPopupSize(self, **kwargs):
        rect = kwargs['rect_out']
        self.popup_pos = (rect[0], rect[1])
        self.popup_img = PNMImage(rect[2], rect[3])
        self.popup_img.add_alpha()

    def OnPaint(self, **kwargs):
        browser = kwargs['browser']
        element_type = kwargs['element_type']
        paint_buffer = kwargs['paint_buffer']
        width = kwargs['width']
        height = kwargs['height']

        if element_type == cefpython.PET_VIEW:
            tex = self.texture
            if width != tex.get_x_size() or height != tex.get_y_size():
                return
            tex.set_ram_image(paint_buffer.GetString(mode="bgra", origin="bottom-left"))

            if self.popup_show:
                px, py = self.popup_pos
                tex.load_sub_image(self.popup_img, px, py, 0, 0)
        elif element_type == cefpython.PET_POPUP:
            if width != self.popup_img.get_x_size() or height != self.popup_img.get_y_size():
                return
            imgdata = paint_buffer.GetString(mode="rgba", origin="top-left")
            x, y = 0, 0
            for i in range(0, len(imgdata), 4):
                self.popup_img.set_xel_val(x, y, *imgdata[i:i+3])
                #print(self.popup_img.has_alpha(), x, y, imgdata[i+3])
                self.popup_img.set_alpha_val(x, y, imgdata[i+3])

                x += 1
                if x == width:
                    x = 0
                    y += 1
        else:
            raise Exception("Unknown element_type: %s" % element_type)

    def GetViewRect(self, **kwargs):
        browser = kwargs['browser']
        rect_out = kwargs['rect_out']
        rect_out.extend([0, 0, self.texture.get_x_size(), self.texture.get_y_size()])
        return True

    def OnConsoleMessage(self, **kwargs):
        print('{} ({}:{})'.format(
            kwargs['message'],
            kwargs['source'],
            kwargs['line']
        ))

    def OnLoadError(self, **kwargs):
        print("Load Error")
        pprint.pprint(kwargs)


class CEFPanda(object):
    _UI_SCALE = 1.0

    def __init__(self):
        app_settings = {
            #"log_severity": cefpython.LOGSEVERITY_INFO,
            #"release_dcheck_enabled": False,  # Enable only when debugging
            # This directories must be set on Linux
            "windowless_rendering_enabled": True,
            "locales_dir_path": cefpython.GetModuleDirectory()+"/locales",
            "resources_dir_path": cefpython.GetModuleDirectory(),
            "browser_subprocess_path": "%s/%s" % (
                cefpython.GetModuleDirectory(), "subprocess"),
        }
        command_line_settings = {
            "off-screen-rendering-enabled": "",
            "off-screen-frame-rate": "60",
            "disable-gpu": "",
            "disable-gpu-compositing": "",
        }

        cefpython.Initialize(app_settings, command_line_settings)
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

        base.accept('mouse1', self._handle_mouse, [False])
        base.accept('mouse1-up', self._handle_mouse, [True])

        base.taskMgr.add(self._cef_message_loop, "CefMessageLoop")

        def shutdown_cef():
            cefpython.Shutdown()

        atexit.register(shutdown_cef)

        self.use_mouse = True

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

    def _handle_mouse(self, mouseup):
        if not self.use_mouse or not base.mouseWatcherNode.has_mouse():
            return

        mouse = base.mouseWatcherNode.getMouse()
        rx, ry = mouse.get_x(), mouse.get_y()
        x = (rx + 1.0) / 2.0 * self._cef_texture.get_x_size()
        y = (ry + 1.0) / 2.0 * self._cef_texture.get_y_size()
        y = self._cef_texture.get_y_size() - y

        self.browser.SendMouseClickEvent(
            x,
            y,
            cefpython.MOUSEBUTTON_LEFT,
            mouseup,
            1,
            cefpython.EVENTFLAG_NONE
        )

    def _cef_message_loop(self, task):
        cefpython.MessageLoopWork()
        self.browser.SendFocusEvent(True)

        if self.use_mouse and base.mouseWatcherNode.has_mouse():
            mouse = base.mouseWatcherNode.getMouse()
            rx, ry = mouse.get_x(), mouse.get_y()
            x = (rx + 1.0) / 2.0 * self._cef_texture.get_x_size()
            y = (ry + 1.0) / 2.0 * self._cef_texture.get_y_size()
            y = self._cef_texture.get_y_size() - y
            self.browser.SendMouseMoveEvent(x, y, mouseLeave=False)

        return task.cont
