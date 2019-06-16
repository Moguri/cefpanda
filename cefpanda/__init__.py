import atexit
import os
import pprint
import sys


from cefpython3 import cefpython
import panda3d.core as p3d


class CefClientHandler:
    browser = None
    texture = None


    def __init__(self, browser, texture):
        self.browser = browser
        self.texture = texture
        self.popup_img = p3d.PNMImage(0, 0)
        self.popup_pos = [0, 0]
        self.popup_show = False

    def OnPopupShow(self, **kwargs): #pylint: disable=invalid-name
        self.popup_show = kwargs['show']

    def OnPopupSize(self, **kwargs): #pylint: disable=invalid-name
        rect = kwargs['rect_out']
        self.popup_pos = (rect[0], rect[1])
        self.popup_img = p3d.PNMImage(rect[2], rect[3])
        self.popup_img.add_alpha()

    def OnPaint(self, **kwargs): #pylint: disable=invalid-name
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
                posx, posy = self.popup_pos
                tex.load_sub_image(self.popup_img, posx, posy, 0, 0)
        elif element_type == cefpython.PET_POPUP:
            if width != self.popup_img.get_x_size() or height != self.popup_img.get_y_size():
                return
            imgdata = paint_buffer.GetString(mode="rgba", origin="top-left")
            posx, posy = 0, 0
            for i in range(0, len(imgdata), 4):
                self.popup_img.set_xel_val(posx, posy, *imgdata[i:i+3])
                #print(self.popup_img.has_alpha(), posx, posy, imgdata[i+3])
                self.popup_img.set_alpha_val(posx, posy, imgdata[i+3])

                posx += 1
                if posx == width:
                    posx = 0
                    posy += 1
        else:
            raise Exception("Unknown element_type: %s" % element_type)

    def GetViewRect(self, **kwargs): #pylint: disable=invalid-name
        rect_out = kwargs['rect_out']
        rect_out.extend([0, 0, self.texture.get_x_size(), self.texture.get_y_size()])
        return True

    def OnConsoleMessage(self, **kwargs): #pylint: disable=invalid-name
        print('{} ({}:{})'.format(
            kwargs['message'],
            kwargs['source'],
            kwargs['line']
        ))

    def OnLoadError(self, **kwargs): #pylint: disable=invalid-name
        print("Load Error")
        pprint.pprint(kwargs)


class CEFPanda(object):
    _UI_SCALE = 1.0

    def __init__(self):
        cef_mod_dir = cefpython.GetModuleDirectory()
        app_settings = {
            "windowless_rendering_enabled": True,
            "locales_dir_path": os.path.join(cef_mod_dir, 'locales'),
            "resources_dir_path": cefpython.GetModuleDirectory(),
            "browser_subprocess_path": os.path.join(cef_mod_dir, 'subprocess'),
        }
        command_line_settings = {
        }

        cefpython.Initialize(app_settings, command_line_settings)
        self._cef_texture = p3d.Texture()
        self._cef_texture.set_compression(p3d.Texture.CMOff)
        self._cef_texture.set_component_type(p3d.Texture.TUnsignedByte)
        self._cef_texture.set_format(p3d.Texture.FRgba4)

        card_maker = p3d.CardMaker("browser2d")
        card_maker.set_frame(-self._UI_SCALE, self._UI_SCALE, -self._UI_SCALE, self._UI_SCALE)
        node = card_maker.generate()
        self._cef_node = base.render2d.attachNewNode(node)
        self._cef_node.set_texture(self._cef_texture)
        self._cef_node.set_transparency(p3d.TransparencyAttrib.MAlpha)

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

        self.browser.SendFocusEvent(True)
        self._set_browser_size()
        base.accept('window-event', self._set_browser_size)

        base.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        base.accept('keystroke', self._handle_text)
        base.accept('arrow_left', self._handle_key, [cefpython.VK_LEFT])
        base.accept('arrow_right', self._handle_key, [cefpython.VK_RIGHT])
        base.accept('arrow_up', self._handle_key, [cefpython.VK_UP])
        base.accept('arrow_down', self._handle_key, [cefpython.VK_DOWN])
        base.accept('home', self._handle_key, [cefpython.VK_HOME])
        base.accept('end', self._handle_key, [cefpython.VK_END])

        base.accept('mouse1', self._handle_mouse, [False])
        base.accept('mouse1-up', self._handle_mouse, [True])

        base.taskMgr.add(self._cef_message_loop, "CefMessageLoop")

        def shutdown_cef():
            cefpython.Shutdown()

        atexit.register(shutdown_cef)

        self.use_mouse = True

    def _load_end(self, *_args, **_kwargs):
        self._is_loaded = True

        # Execute any queued javascript
        for i in self._js_onload_queue:
            self.execute_js(i)

        self._js_onload_queue = []

    #probably due to the latest versions, the load string doesn't work that well
    #so we are loading the string via an url
    def load_string(self, string):
        self.load(f'data:text/html,{string}')

    def load(self, url):
        self.browser.SetJavascriptBindings(self.jsbindings)
        if url:
            if not url.startswith('data'):
                url = os.path.abspath(url)
                if sys.platform != 'win32':
                    url = 'file://' + url
            self._is_loaded = False
            self.browser.GetMainFrame().LoadUrl(url)
        else:
            self.browser.GetMainFrame().LoadUrl('about:blank')

    def execute_js(self, js_string, onload=False):
        if onload and not self._is_loaded:
            self._js_onload_queue.append(js_string)
        else:
            self.browser.GetMainFrame().ExecuteJavascript(js_string)

    def set_js_function(self, name, func):
        self.jsbindings.SetFunction(name, func)
        self.jsbindings.Rebind()

    def _set_browser_size(self, _window=None):
        width = int(round(base.win.getXSize() * self._UI_SCALE))
        height = int(round(base.win.getYSize() * self._UI_SCALE))

        # We only want to resize if the window size actually changed.
        if self._cef_texture.get_x_size() != width and self._cef_texture.get_y_size() != height:
            self._cef_texture.set_x_size(width)
            self._cef_texture.set_y_size(height)

            # Clear the texture
            img = p3d.PNMImage(width, height)
            img.fill(0, 0, 0)
            img.alpha_fill(0)
            self._cef_texture.load(img)
            self.browser.WasResized()

    def _handle_key(self, keycode):
        keyevent = {
            'type': cefpython.KEYEVENT_RAWKEYDOWN,
            'windows_key_code': keycode,
            'character': keycode,
            'unmodified_character': keycode,
            'modifiers': cefpython.EVENTFLAG_NONE,
        }
        self.browser.SendKeyEvent(keyevent)

        keyevent['type'] = cefpython.KEYEVENT_KEYUP
        self.browser.SendKeyEvent(keyevent)

    def _handle_text(self, keyname):
        keycode = ord(keyname)
        text_input = keycode not in [
            7, # escape
            8, # backspace
            9, # tab
            127, # delete
        ]

        keyevent = {
            'windows_key_code': keycode,
            'character': keycode,
            'unmodified_character': keycode,
            'modifiers': cefpython.EVENTFLAG_NONE,
        }

        if text_input:
            keyevent['type'] = cefpython.KEYEVENT_CHAR
        else:
            keyevent['type'] = cefpython.KEYEVENT_RAWKEYDOWN
        self.browser.SendKeyEvent(keyevent)

        keyevent['type'] = cefpython.KEYEVENT_KEYUP
        self.browser.SendKeyEvent(keyevent)

    def _get_mouse_pos(self):
        mouse = base.mouseWatcherNode.getMouse()
        posx = (mouse.get_x() + 1.0) / 2.0 * self._cef_texture.get_x_size()
        posy = (mouse.get_y() + 1.0) / 2.0 * self._cef_texture.get_y_size()
        posy = self._cef_texture.get_y_size() - posy

        return posx, posy

    def _handle_mouse(self, mouseup):
        if not self.use_mouse or not base.mouseWatcherNode.has_mouse():
            return

        posx, posy = self._get_mouse_pos()

        self.browser.SendMouseClickEvent(
            posx,
            posy,
            cefpython.MOUSEBUTTON_LEFT,
            mouseup,
            1,
            cefpython.EVENTFLAG_NONE
        )

    def _cef_message_loop(self, task):
        cefpython.MessageLoopWork()

        if self.use_mouse and base.mouseWatcherNode.has_mouse():
            posx, posy = self._get_mouse_pos()
            self.browser.SendMouseMoveEvent(posx, posy, mouseLeave=False)

        return task.cont
