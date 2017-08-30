import wx
import requests
import subprocess
from xml.dom import minidom
from wakeonlan import wol
import os.path
from functools import lru_cache, partial
import logging

LAYOUT = [
    ['spacer_button_1_of_2', 'power'],
    ['back', 'home'],
    ['top_left_corner', 'up', 'top_right_corner'],
    ['left', 'ok', 'right'],
    ['bottom_left_corner', 'down', 'bottom_right_corner'],
    ['replay', 'info'],
    ['previous', 'play', 'next'],
    ['vol_down', 'vol_up', 'vol_mute'],
    ['app_BloombergTV', 'app_Twitch'],
    ['app_Plex', 'app_YouTube'],
]

BUTTON_MAPPING = {
    'back': lambda e: post_keypress('Back'),
    'home': lambda e: post_keypress('Home'),
    'up': lambda e: post_keypress('Up'),
    'left': lambda e: post_keypress('Left'),
    'ok': lambda e: post_keypress('Select'),
    'right': lambda e: post_keypress('Right'),
    'down': lambda e: post_keypress('Down'),
    'replay': lambda e: post_keypress('InstantReplay'),
    'info': lambda e: post_keypress('Info'),
    'previous': lambda e: post_keypress('Rev'),
    'play': lambda e: post_keypress('Play'),
    'next': lambda e: post_keypress('Fwd'),
    'power': lambda e: power_button_keypress(),
    'vol_down': lambda e: post_keypress('VolumeDown'),
    'vol_up': lambda e: post_keypress('VolumeUp'),
    'vol_mute': lambda e: post_keypress('VolumeMute'),
}

MAC_ADDRESS = 'FF:FF:FF:FF:FF:FF'
IP_ADDRESS = '192.168.3.21'
PORT = 8060
BASE_URL="http://%s:%s" % (IP_ADDRESS, PORT)
WOL_BROADCAST_ADDRESS = '255.255.255.255'
TV_ON_CHECK_TIMEOUT = 0.1

def scale_bitmap(bitmap, width, height):
    image = bitmap.ConvertToImage()
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.Bitmap(image)
    return result

def post_keypress(key):
    requests.post("%s/keypress/%s" % (BASE_URL, key), timeout=TV_ON_CHECK_TIMEOUT)

def power_button_keypress():
    try:
        resp = requests.get("%s/query/device-info" % BASE_URL, timeout=TV_ON_CHECK_TIMEOUT)
        xml_doc = minidom.parseString(resp.content)
        if xml_doc.getElementsByTagName('power-mode')[0].firstChild.data == 'DisplayOff':
            power_on()
            return
    except requests.exceptions.Timeout:
        # if the request times out, we know the TV is off
        power_on()
        return
    post_keypress('PowerOff')

def power_on():
    wol.send_magic_packet(MAC_ADDRESS)
    post_keypress('Power')

@lru_cache(maxsize=1)
def list_installed_apps():
    apps = {} 
    try:
        resp = requests.get("%s/query/apps" % BASE_URL, timeout=TV_ON_CHECK_TIMEOUT)
        xml_doc = minidom.parseString(resp.content)
        for node in xml_doc.getElementsByTagName('app'):
            apps[node.firstChild.data] = node.getAttribute('id')
    except requests.exceptions.Timeout:
        # if the request times out, we know the TV is off
        logging.error("Timed out trying to get the list of installed apps, " \
        "are you sure the Roku is on?")
    return apps

def launch_app(app_name, _):
    # pretty sure app names are limited to alphanumeric and spaces
    apps = list_installed_apps()
    if app_name not in apps:
        logging.error("App %s not found in list of installed apps: %s" % \
                (app_name, apps.keys()))
    else:
        try:
            requests.post("%s/launch/%s" % (BASE_URL, apps[app_name]), timeout=TV_ON_CHECK_TIMEOUT)
        except:
            # seems the roku violates HTTP and doesn't send a response back
            pass

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(400,800))
        self.remote = wx.Panel(self)
        self.remote.Bind(wx.EVT_PAINT, self.OnPaint)

        remote_content = wx.BoxSizer(wx.VERTICAL)
        for row in LAYOUT:
            remote_content_row = wx.BoxSizer(wx.HORIZONTAL)
            for i,element in enumerate(row):
                if element[:3] == 'app':
                    # check and see if the button image exists for it                    
                    image_name = "images/blank_button_%d_of_2.png" % (i+1)
                    if os.path.isfile("images/%s.png" % element):
                        image_name = "images/%s.png" % element
                    button = wx.StaticBitmap(self.remote, -1,
                        wx.Bitmap(image_name, wx.BITMAP_TYPE_ANY))
                    remote_content_row.Add(button)
                    button.Bind(wx.EVT_LEFT_UP, partial(launch_app, element[4:]))
                else:
                    button = wx.StaticBitmap(self.remote, -1,
                        wx.Bitmap("images/%s.png" % element, wx.BITMAP_TYPE_ANY))
                    remote_content_row.Add(button)
                    if element in BUTTON_MAPPING:
                        button.Bind(wx.EVT_LEFT_UP, BUTTON_MAPPING[element])

            remote_content.Add(remote_content_row)

        remote_with_sides = wx.BoxSizer(wx.HORIZONTAL)
        remote_with_sides.Add(wx.StaticBitmap(self.remote, -1,
            scale_bitmap(wx.Bitmap("images/left_edge.png", wx.BITMAP_TYPE_ANY),
                31, 56.5*len(LAYOUT))))
        remote_with_sides.Add(remote_content)
        remote_with_sides.Add(wx.StaticBitmap(self.remote, -1,
            scale_bitmap(wx.Bitmap("images/right_edge.png", wx.BITMAP_TYPE_ANY),
                30, 56.5*len(LAYOUT))))

        remote_sizer = wx.BoxSizer(wx.VERTICAL)
        remote_sizer.Add((0,0), 1, wx.EXPAND)
        remote_sizer.Add(wx.StaticBitmap(self.remote, -1,
            wx.Bitmap("images/top_edge.png" , wx.BITMAP_TYPE_ANY)))
        remote_sizer.Add(remote_with_sides,
                wx.CENTER)
        remote_sizer.Add(wx.StaticBitmap(self.remote, -1,
            wx.Bitmap("images/bottom_edge.png" , wx.BITMAP_TYPE_ANY)))
        remote_sizer.Add((0,0), 1, wx.EXPAND)

        window_sizer = wx.BoxSizer(wx.HORIZONTAL)
        window_sizer.Add((0,0), 1, wx.EXPAND)
        window_sizer.Add(remote_sizer, wx.CENTER)
        window_sizer.Add((0,0), 1, wx.EXPAND)

        self.remote.SetSizer(window_sizer)

        self.Show()


    def OnPaint(self, e):
        dc = wx.PaintDC(self.remote)
        brush = wx.Brush('black')
        dc.SetBackground(brush)
        dc.Clear()

app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.
window = MainWindow(None, 'RokuTV Remote') # A Frame is a top-level window.
app.MainLoop()
