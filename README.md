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
| `p` | pause | pause cleaning（ok）  |
| `r` | resume | |
| `h` | stop  | （ok）  |
| `wash`  | Washing       | Washing the mop  （ok）            |
| `washpause`  | washpause       | washpause the mop   （ok）           |

Note

清扫状态，请求成功时存在。

s-清扫中，p-暂停中，h-空闲中，goposition-正在前往指定位置，gopositionpause-在指定点停止，findpet-寻找宠物，findpetpause-寻找宠物暂停，cruise-巡航中，cruisepause-巡航暂停，buildmap-创建地图，buildmappause-建图暂停

控制命令
~~~
"s":开始清扫
"r":恢复清扫
"p":暂停清扫
"h":停止清扫
~~~

chargeSt

| Code | Full State | Description                |
| ---- | ---------- | -------------------------- |
| `i`  | idle       | Not charging  （ok）          |
| `g`  |  go charging     |  return-to-charge       ok    |
| `charging`  | charging     | charging On dock    ok        |
| `gp`  |      |        |

Note

充电状态，请求成功时存在。

g-正在回充，gp-回充暂停，i-空闲，sc-底座充电，wc-线充，charging-充电中（包括SC和WC）

控制回充命令
~~~
"go-start":开始回充
"stopGo":结束回充
~~~


stationSt

| Code | Full State | Description                |
| ---- | ---------- | -------------------------- |
| `i`  | idle       | Station is idle    （ok）        |
| `dry`  | drying     | Drying the mop      （ok）       |
| `dust`  | emptying   | Emptying dustbin     （ok）      |
| `dustpause`  | emptying   | Emptying dustbin  （ok）         |

Note

基站状态

i-空闲，wash-正在清洗拖布，dry-正在烘干，drypause-烘干暂停，dust-集尘中，dustpause-集尘暂停，clean-基站清洁，cleanpause-基站清洁暂停，wash-清洗拖布，washpause-清洗拖布暂停


doc:

https://open.ecovacs.com/#/skill/plaza/ecovacs-robot-control-en
