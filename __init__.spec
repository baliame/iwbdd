# -*- mode: python -*-

block_cipher = None


a = Analysis(['iwbdd\\__init__.py', 'iwbdd\\audio_data.py', 'iwbdd\\background.py', 'iwbdd\\bossfight.py', 'iwbdd\\common.py', 'iwbdd\\editor.py', 'iwbdd\\game.py', 'iwbdd\\iwbdd.py', 'iwbdd\\lens.py', 'iwbdd\\moving_platform.py', 'iwbdd\\object.py', 'iwbdd\\object_importer.py', 'iwbdd\\pickups.py', 'iwbdd\\player.py', 'iwbdd\\pygame_oo', 'iwbdd\\screen.py', 'iwbdd\\spritesheet.py', 'iwbdd\\tileset.py', 'iwbdd\\world.py', 'iwbdd\\pygame_oo\\__init__.py', 'iwbdd\\pygame_oo\\main_loop.py', 'iwbdd\\pygame_oo\\window.py'],
             pathex=['C:\\Users\\dxmia\\munka\\iwbdd'],
             binaries=[],
             datas=[('audio.dat', '.'), ('tilesets.tls', '.'), ('backgrounds.bgs', '.'), ('spritesheets.sss', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='__init__',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
