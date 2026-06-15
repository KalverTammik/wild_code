# Works Geometry Sync - Technical Summary

## Eesmärk

Seda dokumenti kasutatakse praeguse `Works` mooduli geomeetria sünkroonimise töö kirjeldamiseks, et hoida kogu tehniline info ühes kohas.

## Praegune olukord

- `Works` moodul loob QGIS-i töökihi punkt-featuuri ja hoiab geomeetriat kaardil.
- Backendis salvestatakse seni geomeetria ainult vabal kujul töö `description` väljal HTML-metaandmetena.
- `WorksSyncService` on seni kasutanud geomeetria sünkroonimiseks ja tagasisideks ainult `description` uuendamist.
- Backend taski päringud ei taasalusta `geometry` välja ja `createTask` ei kasutanud geomeetriat esmalt.

## Praegused failid ja funktsioonid, millega tegeleme

### GraphQL / API-kihi failid

- `python/queries/graphql/tasks/w_tasks_module_data_by_item_id.graphql`
  - lisatud `geometry` tagastusväli taski andmete päringusse.
- `python/queries/graphql/tasks/ListFilteredTasks.graphql`
  - lisatud `geometry` tagastusväli massipäringusse taskide jaoks.
- `python/queries/graphql/tasks/updateTaskGeometry.graphql`
  - lisatud uus mutatsioon taski `geometry` välja uuendamiseks.
- `python/api_actions.py`
  - `APIModuleActions.create_task(...)` sai valikulise `geometry` parameetri.
  - `APIModuleActions.update_task_geometry(...)` lisatud taski geomeetria uuendamiseks.
  - `create_task` saab nüüd proovida taski loomist esmalt geomeetriaga ja vajadusel taaskäivitada ilma `geometry` parameetrita, kui backend seda ei toeta.

### Works mooduli failid

- `modules/works/works_layer_service.py`
  - lisatud `backend_geometry_payload_from_geometry(...)` QGIS-i `QgsGeometry` serialiseerimiseks backendile sobivaks JSON-ks.
  - lisatud `geometry_from_payload(...)` backendist tuleva `geometry` deserialiseerimiseks `QgsGeometry`-ks.
  - parandatud `_field_type_matches()` nii, et ka `QString` tüüpi väljad sobivad integer-ülesannetega legacy-kihil.
- `modules/works/works_sync_service.py`
  - ülesehitus sünkroonimisega backendist: `geometry` laetakse taski andmetest ja rakendatakse kihile.
  - QGIS-i geomeetria muutus edastatakse backendisse `APIModuleActions.update_task_geometry(...)` kaudu.
  - säilitatakse kirjeldusmetaandmete `WorksDescriptionService` värskendamine, et tagada olemasoleva töövoo ühilduvus.
- `modules/works/works_create_controller.py`
  - taski loomisel saadetakse backendile punktgeomeetria `geometry` väljaga.

## Kasutatav tehnoloogia

- QGIS Python plugin: `PyQt5`, `qgis.core`, `qgis.gui`.
- Graafik API: GraphQL kaudu `APIClient.send_query(...)`.
- Taski mudel: `Task` (moodul `Module.TASK.value`).
- Geomeetria formaat: GeoJSON-laadne objekt `{"type":"Point","coordinates":[x,y]}`.
- Töökäsu punkt jääb ainsaks backendile saadetavaks geomeetriaks.
- Lähedal asuvaid veevõrgu või kanalisatsioonivõrgu elemente praegu payloadi ei lisata.
- Logimine: `PythonFailLogger` ja `ModernMessageDialog` kasutamine veateadete jaoks.

## Muudatused praegu töös

- Backend geomeetria integreerimine `Works` taski loomisesse.
- Backendist laetud taski `geometry` sünkroonimine QGIS kihiga.
- QGIS-i geomeetria muutuste pushimine backendisse `geometry` välja kaudu.
- Taski loomise ebaõnnestumise leebem käitumine juhul, kui backend ei toeta `geometry` sisendit.
- `Works` kihi rakenduste tugi olemasolevate string-tüüpi väljadega (nt `ext_job_type`).

## Praegused piirangud

- `Works` kiht on punkt-kiht; praegu ei toetata siinkohal teisi geomeetriatüüpe `Works` moodulis.
- Kui backend ei toeta `createTask` `geometry` parameetrit, tehakse fallback ilma geomeetriata.
- Backend `geometry` väljale tugi peab olema tegelikult olemas ja sobivalt struktureeritud.

## Järgmised sammud

1. Testida `Works` mooduli taski loomist tegelikus pluginis ning kontrollida, kas `create_task` edastab geomeetria ja kas tagastus on edukas.
2. Kontrollida backend `updateTaskGeometry` mutatsiooni toimivust ning sünkroonimist QGIS-i `committedGeometriesChanges` kaudu.
3. Kui vajalik, eemaldada järjest kirjeldusmetaandmete geomeetria roll backendis ja liigutada geomeetria täielikult `geometry` väljale.
4. Kaardistada sarnane lahendus teiste geomeetriapõhiste moodulitega:
   - `projects`
   - `easements`
   - `asbuilt`
5. Lisada täpsem logimine ja võimalusel monitorida GraphQL vastuseid veamõistetega, et leida täpne katkestuskoht backendis.

## Märkused

- Praegune töö on esmalt `Works` mooduli audit ja geomeetria sünkroniseerimise prototüüp.
- Eesmärk on luua selge piir `description` metaandmete ja eraldiseisva `geometry` välja vahel.
- Dokumenteeritud lähenemine aitab hilisematel laiendustel sarnaseid muudatusi uuesti rakendada.
