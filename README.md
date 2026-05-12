# Ecovacs API

Call the gateway via HTTP

## Three-step flow

Configure AK → 2. List devices → 3. Send commands

step 1. get AK (Access Key)

Open the Ecovacs Open Platform in a browser and get the AK.

Mainland China: https://open.ecovacs.cn/

or

International: https://open.ecovacs.com/




~~~
Ecovacs data from vacuum.py: {'cleanSt': 'h', 'chargeSt': 'g', 'stationSt': 'i'}
Ecovacs data from vacuum.py: {'cleanSt': 'p', 'chargeSt': 'i', 'stationSt': 'i'}
Ecovacs data from vacuum.py: {'cleanSt': 'p', 'chargeSt': 'charging', 'stationSt': 'i'}
Ecovacs data from vacuum.py: {'cleanSt': 'washpause', 'chargeSt': 'charging', 'stationSt': 'i'}
Ecovacs data from vacuum.py: {'cleanSt': 'wash', 'chargeSt': 'charging', 'stationSt': 'i'}

~~~


https://open.ecovacs.com/#/skill/plaza/ecovacs-robot-control-en
