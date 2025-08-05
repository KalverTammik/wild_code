


OpenAI Python teegi paigaldamine QGIS-i jaoks (Eesti keeles):


1. Ava Windows PowerShell (soovitatav) või Command Prompt.
2. Leia fail nimega python-qgis-ltr.bat oma QGIS paigalduse kaustas. Näide tee kohta (asenda see vastavalt oma arvutis QGIS-i asukohaga!):
   C:\QGIS_PATH\bin\python-qgis-ltr.bat

3. Kopeeri ja kleebi allolevad käsud ükshaaval ning vajuta Enter pärast iga käsku (kasuta kindlasti PowerShellis alguses & märki ja pane tee jutumärkidesse!):

   & "C:\QGIS_PATH\bin\python-qgis-ltr.bat" -m pip install --upgrade pip
   & "C:\QGIS_PATH\bin\python-qgis-ltr.bat" -m pip install openai

Selgitus:
- Asenda C:\QGIS_PATH\bin\python-qgis-ltr.bat tegeliku teega, kus Sinu arvutis asub QGIS (näiteks C:\Program Files\QGIS 3.40.9\bin\python-qgis-ltr.bat).
- Kui QGIS on paigaldatud mujale, kasuta vastavat teed.
- Tee peab alati olema jutumärkides, kui see sisaldab tühikuid.
- PowerShellis peab käsu alguses olema & (call operator), kui tee on jutumärkides.
- Kui käsud õnnestuvad, taaskäivita QGIS.
- Kui saad hoiatuse, et pip.exe või muu skript on "AppData\\Roaming\\Python" kaustas, võid selle hoiatuse ignoreerida või lisada selle kausta PATH-i.

NB! Ära kasuta qgis-ltr-bin.exe pip paigaldamiseks – see avab QGIS-i graafilise liidese, mitte õiget Pythoni!

Märkused:
- Kui QGIS on paigaldatud mujale, kasuta vastavat teed.
- Tee peab alati olema jutumärkides, kui see sisaldab tühikuid.
- PowerShellis peab käsu alguses olema & (call operator), kui tee on jutumärkides.
- Kui käsud õnnestuvad, taaskäivita QGIS.
- Kui saad hoiatuse, et pip.exe või muu skript on "AppData\\Roaming\\Python" kaustas, võid selle hoiatuse ignoreerida või lisada selle kausta PATH-i.

Kui vajad abi, pöördu oma IT-tugiisiku poole või vaata QGIS dokumentatsiooni.
