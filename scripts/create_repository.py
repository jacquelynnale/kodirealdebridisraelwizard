#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Israel Wizard - Repository Generator
Creates addons.xml, MD5 checksums, and ZIP packages for Kodi repository.

Usage: python create_repository.py [--zip] [--release VERSION]
"""

import os
import sys
import hashlib
import zipfile
import argparse
from xml.etree import ElementTree
from xml.dom import minidom

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDONS = ['plugin.program.israelwizard', 'repository.israelwizard']
OUTPUT_DIR = REPO_ROOT  # addons.xml in root
ZIPS_DIR = os.path.join(REPO_ROOT, 'zips')

def calculate_md5(filepath):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# ... (skip get_addon_xml) ...

# ... (skip generate_addons_xml) ...

def save_addons_xml(content):
    """Save addons.xml and generate MD5."""
    # Save addons.xml to root
    addons_path = os.path.join(OUTPUT_DIR, 'addons.xml')
    with open(addons_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[OK] Generated: addons.xml')
    
    # Generate and save MD5
    md5_hash = calculate_md5(addons_path)
    md5_path = os.path.join(OUTPUT_DIR, 'addons.xml.md5')
    with open(md5_path, 'w', encoding='utf-8') as f:
        f.write(md5_hash)
    print(f'[OK] Generated: addons.xml.md5 ({md5_hash})')


def create_addon_zip(addon_name, version=None):
    """Create SIMPLE ZIP package to prevent Kodi crash."""
    addon_path = os.path.join(REPO_ROOT, addon_name)
    if not os.path.isdir(addon_path):
        print(f'✗ Addon not found: {addon_name}')
        return None
    
    # Get version
    if not version:
        addon_xml_path = os.path.join(addon_path, 'addon.xml')
        tree = ElementTree.parse(addon_xml_path)
        version = tree.getroot().get('version', '1.0.0')
    
    # Ensure zips output dir exists
    addon_zips_dir = os.path.join(ZIPS_DIR, addon_name)
    os.makedirs(addon_zips_dir, exist_ok=True)
    
    zip_name = f'{addon_name}-{version}.zip'
    zip_path = os.path.join(addon_zips_dir, zip_name)
    
    print(f'Creating ZIP: {zip_path}...')
    
    # Standard ZIP creation (Best compatibility)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Walk the addon directory
        for root, dirs, files in os.walk(addon_path):
            # EXCLUDE everything irrelevant
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.idea', 'zips', 'releases', 'bin', 'obj']]
            
            for file in files:
                if file.endswith(('.pyc', '.pyo', '.DS_Store', '.zip')):
                    continue
                
                abs_path = os.path.join(root, file)
                
                # Critical: Calculate path inside ZIP
                # Must be: addon_id/file.xml
                # NOT: addon_id/addon_id/file.xml
                
                rel_path = os.path.relpath(abs_path, addon_path) # path relative to addon folder
                zip_arcname = os.path.join(addon_name, rel_path) # addon_id/rel_path
                
                # FORCE FORWARD SLASHES (Critical for Kodi/Zip standard)
                zip_arcname = zip_arcname.replace(os.sep, '/')
                
                zf.write(abs_path, zip_arcname)
    
    # Verify ZIP integrity
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            ret = zf.testzip()
            if ret is not None:
                print(f'❌ Corrupted file in ZIP: {ret}')
                return None
            print(f'✅ ZIP Entry Check Passed: {zip_path}')
    except Exception as e:
        print(f'❌ ZIP Validation Failed: {e}')
        return None

    print(f'[OK] Created Safe ZIP: {zip_path}')
    return zip_path


def get_addon_xml(addon_path):
    """Parse and return addon.xml content."""
    addon_xml_path = os.path.join(addon_path, 'addon.xml')
    if not os.path.exists(addon_xml_path):
        return None
    
    with open(addon_xml_path, 'r', encoding='utf-8') as f:
        return f.read()


def generate_addons_xml():
    """Generate addons.xml from all addon folders."""
    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    
    for addon_name in ADDONS:
        addon_path = os.path.join(REPO_ROOT, addon_name)
        if not os.path.isdir(addon_path):
            continue
        
        addon_xml = get_addon_xml(addon_path)
        if addon_xml:
            # Extract addon element
            root = ElementTree.fromstring(addon_xml)
            addon_str = ElementTree.tostring(root, encoding='unicode')
            addons_xml += f'    {addon_str}\n'
            print(f'[OK] Added: {addon_name}')
    
    addons_xml += '</addons>\n'
    return addons_xml


def save_addons_xml(content):
    """Save addons.xml and generate MD5."""
    # Save addons.xml to root
    addons_path = os.path.join(OUTPUT_DIR, 'addons.xml')
    with open(addons_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[OK] Generated: addons.xml')
    
    # Generate and save MD5
    md5_hash = calculate_md5(addons_path)
    md5_path = os.path.join(OUTPUT_DIR, 'addons.xml.md5')
    with open(md5_path, 'w', encoding='utf-8') as f:
        f.write(md5_hash)
    print(f'[OK] Generated: addons.xml.md5 ({md5_hash})')


def create_addon_zip(addon_name, version=None):
    """Create ZIP package for an addon in zips/addon_id/."""
    addon_path = os.path.join(REPO_ROOT, addon_name)
    if not os.path.isdir(addon_path):
        print(f'✗ Addon not found: {addon_name}')
        return None
    
    # Get version from addon.xml if not provided
    if not version:
        addon_xml_path = os.path.join(addon_path, 'addon.xml')
        tree = ElementTree.parse(addon_xml_path)
        version = tree.getroot().get('version', '1.0.0')
    
    # Create zips/addon_id/ folder
    addon_zips_dir = os.path.join(ZIPS_DIR, addon_name)
    os.makedirs(addon_zips_dir, exist_ok=True)
    
    zip_name = f'{addon_name}-{version}.zip'
    zip_path = os.path.join(addon_zips_dir, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(addon_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.idea', 'zips', 'releases']]
            
            for file in files:
                if file.endswith(('.pyc', '.pyo', '.DS_Store')):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, REPO_ROOT) # This keeps folder structure 'plugin.program.../file'
                # But for a repo zip, usually we want the folder inside.
                # If we zip 'plugin.program.israelwizard', the zip should contain 'plugin.program.israelwizard/...'
                # arcname from REPO_ROOT achieves this e.g. 'plugin.program.israelwizard/addon.xml'
                zf.write(file_path, arcname)
    
    print(f'[OK] Created: {zip_path}')
    return zip_path


def validate_addon_xml(addon_path):
    """Basic validation of addon.xml."""
    addon_xml_path = os.path.join(addon_path, 'addon.xml')
    
    try:
        tree = ElementTree.parse(addon_xml_path)
        root = tree.getroot()
        
        addon_id = root.get('id')
        version = root.get('version')
        
        if not addon_id:
            print(f'✗ Missing addon id in {addon_xml_path}')
            return False
        
        if not version:
            print(f'✗ Missing version in {addon_xml_path}')
            return False
        
        print(f'[OK] Valid: {addon_id} v{version}')
        return True
        
    except Exception as e:
        print(f'✗ Parse error: {e}')
        return False


def main():
    parser = argparse.ArgumentParser(description='Israel Wizard Repository Generator')
    parser.add_argument('--zip', action='store_true', help='Create ZIP packages')
    parser.add_argument('--release', type=str, help='Version for release')
    parser.add_argument('--validate', action='store_true', help='Validate addon.xml files')
    args = parser.parse_args()
    
    print('=' * 50)
    print('Israel Wizard Repository Generator')
    print('=' * 50)
    
    # Validate
    if args.validate:
        print('\nValidating addons...')
        for addon_name in ADDONS:
            addon_path = os.path.join(REPO_ROOT, addon_name)
            validate_addon_xml(addon_path)
    
    # Generate addons.xml
    print('\nGenerating addons.xml...')
    addons_xml = generate_addons_xml()
    save_addons_xml(addons_xml)
    
    # Create ZIPs
    if args.zip:
        print('\nCreating ZIP packages...')
        for addon_name in ADDONS:
            create_addon_zip(addon_name, args.release)
    
    print('\n[OK] Repository generation complete!')


if __name__ == '__main__':
    main()
