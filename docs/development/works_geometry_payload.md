# Tööde geomeetria Kavitrosse

See dokument kirjeldab, millise `geometry` väärtuse saadab Tööde moodul Kavitrosse ja kuidas see tagasi kaardile loetakse.

## Transport

Geomeetria liigub GraphQL sisendi väljal `geometry` JSON-tekstina: plugin koostab objekti ja serialiseerib selle (`GeometryActions._geometry_input_value`). Sama kuju kasutavad töö loomine (`createTask`) ja asukoha muutmine (`updateTask`, päringufail `updateTaskGeometry.graphql`).

Kui töö asukohas on kinnistu, saadetakse selle seos samas sisendis: `properties: {associate: [<kinnistu id>]}`. Nii ei kulu kinnistu sidumiseks eraldi muutmistoimingut. Kui server sisendi kinnistu tõttu tagasi lükkab, luuakse või liigutatakse töö ilma selleta ja kinnistu seotakse eraldi päringuga (`modules/works/works_create_controller.py`).

```json
{
  "title": "Lekke parandamine",
  "typeId": "task-type-id",
  "statusId": "status-id",
  "geometry": "{\"type\":\"Point\",\"coordinates\":[542123.45,6589123.67],\"icon\":\"fa6-solid:person-digging\",\"color\":\"transparent\",\"iconColor\":\"#9CCC65\"}",
  "properties": {"associate": ["property-id"]}
}
```

## Geomeetria objekti väljad

| Väli | Tüüp | Kohustuslik | Kirjeldus |
| --- | --- | --- | --- |
| `type` | string | jah | GeoJSON geomeetria tüüp, praegu alati `Point`. |
| `coordinates` | array | jah | Töö punkt Tööde kihi CRS-is. |
| `icon` | string | ei | Kavitro kaardi ikoon, `WorksLayerService.BACKEND_GEOMETRY_ICON`. |
| `color` | string | ei | Markeri taust, `transparent`. |
| `iconColor` | string | ei | Ikooni värv: töö staatuse värv hex-kujul. |

Stiiliväljad lisab `GeometryPayloadService.with_style` (`utils/geometry_payload.py`).

## Märkused

- Saadetakse ainult töö enda punkt. Lähedasi vee- või kanalisatsioonivõrgu geomeetriaid ega seotud objektide loendit ei lisata.
- Kaardile tagasi lugemisel kasutatakse sama `Point` objekti Tööde kihi geomeetriana (`WorksLayerService.geometry_for_layer`).
- Kavitro ei kontrolli seda välja (`JSON` skalaar). Kui geomeetria tüüp ei sobi kihiga või koordinaadid ei mahu kihi CRS-i ulatusse, jääb asukoht muutmata ja logitakse `works_sync_geometry_skipped`.
- Iga Kavitrost tulnud asukoha muutus logitakse sündmusena `works_sync_location_moved` koos vana asukohaga.
