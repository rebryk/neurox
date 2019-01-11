# -*- mode: python -*-

block_cipher = None


a = Analysis(['NeuroX.py'],
             pathex=['/Users/rebryk/projects/neurox'],
             binaries=[],
             datas=[],
             hiddenimports=['neuromation'],
             hookspath=['hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='NeuroX',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='icon.icns')

app = BUNDLE(exe,
             Tree('resources', prefix='.'),
             name='NeuroX.app',
             icon='icon.icns',
             bundle_identifier='com.rebryk.neurox',
             info_plist={
                'NSHighResolutionCapable': 'True',
                'LSUIElement': 'True',
                'CFBundleVersion': '1.0.0'
             })
