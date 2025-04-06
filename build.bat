"C:/Program Files/Python313/python.exe" -m nuitka ^
--standalone ^
--windows-console-mode=hide ^
--enable-plugins=tk-inter,pyqt6 ^
--windows-icon-from-ico=pyquick.ico ^
--show-progress ^
--windows-product-name=pyquick ^
--windows-file-version=2.0 ^
--include-data-files=.\pyquick.ico=pyquick.ico ^
--include-data-files=.\error.png=error.png ^
--include-data-files=.\info.png=info.png ^
--include-data-files=.\warning.png=warning.png ^
--include-data-files=.\magic.png=magic.png ^
--include-data-files=.\gpl3.txt=gpl3.txt ^
--follow-imports ^
--remove-output ^
--lto=yes ^
--windows-uac-admin ^
--msvc=latest ^
pyquick.py