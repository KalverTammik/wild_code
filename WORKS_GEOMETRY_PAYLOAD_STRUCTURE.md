# Works Geometry Payload Structure

See dokument kirjeldab `Works` mooduli poolt backendile saadetava `geometry` JSON-i eelduslikku struktuuri.

## Transport

GraphQL sisendis liigub geomeetria `geometry` valja kaudu. Plugin serialiseerib JSON objekti stringiks.

```json
{
  "title": "Lekke parandamine",
  "description": "<p>...</p>",
  "moduleId": "works",
  "typeId": "task-type-id",
  "statusId": "status-id",
  "geometry": "{\"type\":\"Point\",\"coordinates\":[542123.45,6589123.67],\"color\":\"#9CCC65\",\"icon\":\"map-marker\",\"iconColor\":\"#FFFFFF\"}"
}
```

Sama struktuur kehtib `createTask` ja `updateTaskGeometry` korral.

## Geometry JSON

Praegu saadetakse backendile ainult tookasu enda punktgeomeetria.

```json
{
  "type": "Point",
  "coordinates": [542123.45, 6589123.67],
  "color": "#9CCC65",
  "icon": "map-marker",
  "iconColor": "#FFFFFF"
}
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `type` | string | yes | GeoJSON geomeetria tyyp. Praegu `Point`. |
| `coordinates` | array | yes | Tookasu punkti koordinaadid tookihi CRS-is. |
| `color` | string | no | Tookasu markeri taustavarv. |
| `icon` | string | no | Backend kaardi jaoks soovituslik ikooni nimi. |
| `iconColor` | string | no | Ikooni varv hex kujul. |

## Notes

- Lahedal asuvaid veevorgu voi kanalisatsioonivorgu geomeetriaid praegu payloadi ei lisata.
- Payload ei sisalda seotud objektide massiivi ega muid vorgukihtide geomeetriaid.
- QGIS-i tagasi lugemisel kasutatakse sama `Point` objekti tookasu punktkihi geomeetriana.
