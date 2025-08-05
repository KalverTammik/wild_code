# Hinnapakkuja moodul

Moodul kortermajade veevarustuse, kanalisatsiooni ja põrandakütte hinnapakkumiste koostamiseks.

## Struktuur
- `ui/` – kasutajaliidese komponendid (küsimustik, HTML popup)
- `logic/` – äriloogika, arvutused, hinnavahemälu
- `data/` – tüüpsõlmede ja mock-hindade andmed

## Peamised klassid
- `HinnapakkujaModule` – mooduli põhiklass
- `HinnapakkujaDialog` – dialoogi wrapper
- `HinnapakkujaForm` – sisendi küsimustik
- `HinnapakkujaOfferView` – HTML hinnapakkumise vaade
- `HinnapakkujaLogic` – sõlmede ja hindade arvutused
- `PriceCache` – hinnavahemälu

## Laiendatavus
Moodul on loodud nii, et tulevikus saab lisada tööde hinnastuse, salvestusvõimalused, kasutajakontod ja automaatse andmesalvestuse.
