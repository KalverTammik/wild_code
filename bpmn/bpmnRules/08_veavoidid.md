08 – BPMN veavoidid ja nende ennetamine
🎯 Eesmärk
Koguda kokku levinud vead BPMN XML-ide loomisel ja pakkuda lahendused, et skeem avaneks bpmn.io-s ja teistes tööriistades veavabalt.

⚠️ Levinud vead
1) <bpmn:group> probleem
Sümptom: unparsable content <bpmn:group> või unrecognized element <bpmn:group>.

Põhjus: Mõned BPMN tööriistad ei toeta <bpmn:group> elementi (sh bpmn.io XML import).

Lahendus:

Kasuta categoryValueRef ja BPMN-i ametlikku “Group” definitsiooni.

Või asenda group lane’i või sub-process’iga, kui tahad, et elemendid liiguksid koos.

2) unresolved reference vead
Sümptom: unresolved reference <X> või no bpmnElement referenced.

Põhjus: Diagrammi (BPMNShape/BPMNEdge) element viitab olematule BPMN elemendile.

Lahendus:

Kontrolli, et kõik bpmnElement atribuudid viitavad tegelikule ID-le, mis eksisteerib skeemis.

Eemalda kasutamata shape’id ja edge’id.

3) Message vs Signal segadus
Sümptom: Protsessid käivituvad ootamatult või üldse mitte.

Põhjus: Signal on globaalne ja võib vallandada mitu protsessi; Message on suunatud konkreetsele osapoolele.

Lahendus:

Eelista Message Event’e, kui suhtled kindla teise poolega.

Kasuta Signal Event’i ainult siis, kui on vaja mitut protsessi korraga käivitada.

4) Elementide paigutuse probleemid
Sümptom: Lane’id algavad valelt kõrguselt või annavad vale mulje, et kõik aktiveeruvad korraga.

Põhjus: Lane’id pole joondatud signaali/sõnumi alt alguse reegli järgi.

Lahendus:

Joonista lane’i esimene element otse signaali/sõnumi alla.

Väldi tühje lane’e – kasuta empty pool’i, kui protsessi pole.

5) Värvi- ja labelipuudus
Sümptom: LLM-i loodud skeem on raske lugeda.

Põhjus: Elementidel puuduvad selged nimed ja labelid; eristamine ainult värvi abil.

Lahendus:

Lisa labelid kõikidele otsustus- ja lõpp-punktidele.

Kasuta juhendis määratud värvipaletti.

✅ Kontroll enne salvestamist
Ava skeem bpmn.io-s ja veendu, et ei oleks importimisvigu.

Kontrolli, et kõik viited (bpmnElement) on olemas.

Kontrolli, et grupid on kas ametlikus formaadis või asendatud lane/sub-process’iga.

Salvesta fail UTF-8 kodeeringus.

