# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app'],
             binaries=[],
             datas=[
                ('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\ib_insync', 'ib_insync'),
                ('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\trading_ig', 'trading_ig'),
                ('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\res', 'res'),
                ('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\loggers', 'loggers'),
                ('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\settings', 'settings'),
             ],
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
          Tree('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\ib_insync', 'ib_insync'),
            Tree('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\trading_ig', 'trading_ig'),
            Tree('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\res', 'res'),
            Tree('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\loggers', 'loggers'),
            Tree('E:\\freelan\\02_Ongoing\\Asong\\IG_IB_desktop_app\\src\\medoin\\app\\settings', 'settings'),
          a.zipfiles,
          a.datas,
          [],
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
