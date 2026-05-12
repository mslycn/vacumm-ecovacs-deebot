# Ecovacs API

Call the gateway via HTTP

## Three-step flow

Configure AK → 2. List devices → 3. Send commands

step 1. get AK (Access Key)

Open the Ecovacs Open Platform in a browser and get the AK.

Mainland China: https://open.ecovacs.cn/

or

International: https://open.ecovacs.com/



### Ecovacs data examples for deebot x5 pro

~~~
Ecovacs data from vacuum.py: {'cleanSt': 'h', 'chargeSt': 'g', 'stationSt': 'i'}
Ecovacs data from vacuum.py: {'cleanSt': 'p', 'chargeSt': 'i', 'stationSt': 'i'}
Ecovacs data from vacuum.py: {'cleanSt': 'p', 'chargeSt': 'charging', 'stationSt': 'i'}
Ecovacs data from vacuum.py: {'cleanSt': 'washpause', 'chargeSt': 'charging', 'stationSt': 'i'}
Ecovacs data from vacuum.py: {'cleanSt': 'wash', 'chargeSt': 'charging', 'stationSt': 'i'}

~~~



cleanSt


| Code  | Full State | Description                |
| ---- | ---------- | -------------------------- |
| `s` | start cleaning  |    （ok）   |
| `p` | pause |   （ok）  |
| `r` | resume | |
| `h` | stop  | （ok）  |
| `wash`  | Washing       | Washing the mop  （ok）            |
| `washpause`  | washpause       | washpause the mop   （ok）           |

chargeSt

| Code | Full State | Description                |
| ---- | ---------- | -------------------------- |
| `i`  | idle       | Station is idle  （ok）          |
| `g`  |  go charging     |  return-to-charge       ok    |
| `charging`  | charging     |     ok        |



stationSt

| Code | Full State | Description                |
| ---- | ---------- | -------------------------- |
| `i`  | idle       | Station is idle    （ok）        |
| `dry`  | drying     | Drying the mop      （ok）       |
| `dust`  | emptying   | Emptying dustbin     （ok）      |
| `dustpause`  | emptying   | Emptying dustbin  （ok）         |



doc:

https://open.ecovacs.com/#/skill/plaza/ecovacs-robot-control-en
