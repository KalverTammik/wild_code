# confWidgets Module Change Possibilities

This document outlines the types of user preferences or settings that can be defined for each module in the `confWidgets` folder.

---

## Contracts module

- Preferred contract status (e.g., active, pending, closed)
- Preferred contract types (e.g., service, supply, maintenance)
- Default contract template
- Auto-fill fields for new contracts
- Visibility of contract fields in forms

---

## Coordinations module

- Preferred coordination status
- Default responsible person or team
- Notification preferences for coordination updates
- Custom coordination types

---

## Easements module

- Preferred easement types (e.g., road, utility, drainage)
- Default expiration period
- Required documentation fields
- Visibility of easement attributes

---

## Layer Setup module

- Default layer visibility
- Preferred symbology or style
- Default data source or template
- Layer grouping preferences

---

## Project Setup module

- Default project type
- Preferred project status
- Default project folder structure

---

## User Setup module

- no changes needed
---

## Works Setup module

- Preferred work types
- Default scheduling options
- Required documentation for works
- Status tracking preferences

---


> These preferences can be exposed in the UI for user customization, stored in plugin settings, or set as defaults in the code. Actual available preferences depend on the implementation details of each module.