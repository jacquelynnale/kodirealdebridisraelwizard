# -*- coding: utf-8 -*-
"""
Israel Wizard - UI Builder
ישראל וויזארד - בונה ממשק
"""

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import os
import json

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
USERDATA_PATH = xbmcvfs.translatePath('special://userdata/')
ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')

COLORS = {
    'background': 'FF000000', 'secondary': 'FF171717', 'accent': 'FF0066CC',
    'success': 'FF00CC66', 'warning': 'FFCC6600', 'error': 'FFCC0000',
    'text': 'FFFFFFFF', 'text_secondary': 'FFAAAAAA',
}

class UIBuilder:
    def __init__(self):
        self.dialog = xbmcgui.Dialog()
        
    def disable_resource_hogs(self):
        """Disable non-essential services for speed."""
        settings = [
            # specific settings to disable
            {'setting': 'filelists.showparentdiritems', 'value': False}, # Clean UI
            {'setting': 'lookandfeel.enablerssfeeds', 'value': False},  # CPU Saver
            {'setting': 'weather.addon', 'value': ''},                  # CPU Saver
            {'setting': 'audiooutput.guisoundmode', 'value': 0},        # No UI Sounds (Speed)
            {'setting': 'services.esallinterfaces', 'value': False},    # Security/Speed
            {'setting': 'services.upnpserver', 'value': False},         # Security/Speed
        ]
        
        for s in settings:
            try:
                xbmc.executeJSONRPC(json.dumps({
                    'jsonrpc': '2.0', 'method': 'Settings.SetSettingValue',
                    'params': s, 'id': 1
                }))
            except:
                pass
        self.log('Disabled resource hogs')

    def log(self, message, level=xbmc.LOGINFO):
        xbmc.log(f'{ADDON_ID} UIBuilder: {message}', level)
    
    @staticmethod
    def colorize(text, color_key='accent'):
        return f'[COLOR {COLORS.get(color_key, COLORS["text"])}]{text}[/COLOR]'
    
    @staticmethod
    def bold(text):
        return f'[B]{text}[/B]'
    
    @staticmethod
    def rtl_text(text):
        return f'\u200F{text}'
    
    def format_hebrew_label(self, text, color_key=None, bold=False):
        result = self.rtl_text(text)
        if bold:
            result = self.bold(result)
        if color_key:
            result = self.colorize(result, color_key)
        return result
    
    def apply_skin_settings(self):
        try:
            guisettings_source = os.path.join(ADDON_PATH, 'guisettings', 'guisettings.xml')
            guisettings_dest = os.path.join(USERDATA_PATH, 'guisettings.xml')
            if os.path.exists(guisettings_source):
                xbmcvfs.copy(guisettings_source, guisettings_dest)
            
            # Copy advancedsettings.xml (Performance / Firestick)
            advanced_source = os.path.join(ADDON_PATH, 'resources', 'advancedsettings.xml')
            advanced_dest = os.path.join(USERDATA_PATH, 'advancedsettings.xml')
            if os.path.exists(advanced_source):
                xbmcvfs.copy(advanced_source, advanced_dest)
            
            # Configure Netflix Layout
            self.setup_netflix_layout()
            
            # Max Performance Tweaks
            self.disable_resource_hogs()
            
            return True
        except Exception as e:
            self.log(f'Apply settings error: {str(e)}', xbmc.LOGERROR)
            return False
    
    def setup_netflix_layout(self):
        """Configure Arctic Horizon 2 for Netflix style."""
        try:
            skin = xbmcaddon.Addon('skin.arctic.horizon.2')
            
            # 1. Main Menu - Minimalism
            skin.setSetting('home.header.style', 'clean')
            skin.setSetting('home.layout', 'netflix')
            
            # 2. Widgets - Content Rich
            # Define widgets for Movies, TV, Trending
            # Note: In a real scenario, this requires writing to skin shortcuts/overrides
            self.log('Configuring Netflix layout settings...')
            
            # 3. Visuals
            skin.setSetting('color.highlight', 'FF0066CC')  # Blue accent
            skin.setSetting('blur.radius', '20')            # High quality blur
            skin.setSetting('lists.size', 'landscape')      # Landscape thumbs like Netflix
            
            return True
        except Exception as e:
            self.log(f'Netflix layout error: {str(e)}', xbmc.LOGERROR)
            return False

    def set_hebrew_language(self):
        try:
            hebrew_addon = 'resource.language.he_il'
            if not os.path.exists(os.path.join(ADDONS_PATH, hebrew_addon)):
                xbmc.executebuiltin(f'InstallAddon({hebrew_addon})')
                xbmc.sleep(5000)
            xbmc.executeJSONRPC(json.dumps({
                'jsonrpc': '2.0', 'method': 'Settings.SetSettingValue',
                'params': {'setting': 'locale.language', 'value': hebrew_addon}, 'id': 1
            }))
            return True
        except Exception as e:
            self.log(f'Set language error: {str(e)}', xbmc.LOGERROR)
            return False

def apply_skin_settings():
    return UIBuilder().apply_skin_settings()

def set_hebrew_language():
    return UIBuilder().set_hebrew_language()

def colorize(text, color_key='accent'):
    return UIBuilder.colorize(text, color_key)
