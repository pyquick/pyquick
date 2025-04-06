"C:/Program Files/Python313/python.exe" -m nuitka ^
--standalone ^
--windows-console-mode=disable^
--enable-plugins=tk-inter,upx,pyqt6 ^
--windows-icon-from-ico=pyquick.ico ^
--upx-binary=D:\upx\upx.exe ^
--show-progress ^
--windows-product-name=pyquick ^
--windows-file-version=2.0 ^
--include-data-files=.\pyquick.ico=pyquick.ico ^
--include-data-files=.\error.png=error.png ^
--include-data-files=.\info.png=info.png ^
--include-data-files=.\warning.png=warning.png ^
--include-data-files=.\magic.png=magic.png ^
--remove-output ^
--lto=yes ^
--include-module=win32com ^
--msvc=latest ^
pyquick.py