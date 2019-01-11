pip install -r requirements.txt
pyinstaller --clean --onefile NeuroX.spec
npm install -g appdmg
rm dmg/NeuroX.dmg
appdmg dmg/appdmg.json dmg/NeuroX.dmg