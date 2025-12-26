# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import xbmcvfs
import os

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
FIRST_RUN_FILE = os.path.join(ADDON_PROFILE, '.first_run_done')

def log(msg):
    xbmc.log(f'{ADDON_ID}: [Startup] {msg}', xbmc.LOGINFO)

def run():
    if not xbmcvfs.exists(ADDON_PROFILE):
        xbmcvfs.mkdir(ADDON_PROFILE)

    # Check if this is the first run
    if not os.path.exists(FIRST_RUN_FILE):
        log('First run detected! Launching wizard...')
        
        # Create marker file immediately to prevent loops
        with open(FIRST_RUN_FILE, 'w') as f:
            f.write('done')
            
        # Launch the wizard install menu directly
        # Adding a small delay to ensure Kodi is ready
        xbmc.sleep(2000)
        url = f'plugin://{ADDON_ID}/?action=install_menu'
        xbmc.executebuiltin(f'ActivateWindow(Videos,{url},return)')
    else:
        log('Not first run. Skipping auto-launch.')

if __name__ == '__main__':
    run()
