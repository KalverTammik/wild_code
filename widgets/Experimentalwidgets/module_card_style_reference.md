# Module Card Widget Style Reference

The snippets below gather the QSS selectors that style the key widgets used by `ModuleFeedBuilder` so you can reapply the same visuals when working with the UI-only copies in Qt Designer. Each section lists the originating QSS file(s) followed by the relevant selectors.

---

## InfocardHeaderFrame (`styles/Light/ModuleCard.qss`)

```css
QFrame#InfocardHeaderFrame {
    border-bottom: 1px solid rgba(0,120,212,0.25);
    border-left: none;
    border-right: none;
    border-top: none;
    padding: 0;
    margin: 0;
    border-radius: 0;
}

QLabel#ProjectNameLabel {
    color: #111416;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.1px;
}

QLabel#ProjectNumberBadge {
    padding: 1px 4px;
    border-radius: 2px;
    font-size: 10px;
    font-weight: 700;
    color: #0b3d91;
    background: rgba(0,120,212,0.15);
    border: 1px solid rgba(0,120,212,0.50);
    min-width: 24px;
    max-width: 80px;
    text-align: center;
    letter-spacing: 0.2px;
    white-space: nowrap;
    overflow: hidden;
}

QLabel#ProjectClientLabel,
QLabel#ProjectResponsibleLabel,
QLabel#ProjectParticipantsLabel {
    color: #005a9e;
    font-size: 13px;
    font-weight: 500;
    padding: 4px 0px 2px 0px;
}

QLabel#ClientIcon {
    color: rgba(36,41,46,0.85);
}

QLabel#ProjectPrivateIcon {
    background: transparent;
    color: transparent;
}
```

## InfocardHeaderFrame (`styles/Dark/ModuleCard.qss`)

```css
QFrame#InfocardHeaderFrame {
    border-bottom: 1px solid rgba(9,144,143,0.30);
    border-left: none;
    border-right: none;
    border-top: none;
    padding: 0;
    margin: 0;
    border-radius: 0;
}

QLabel#ProjectNameLabel {
    color: #e8e9ef;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.2px;
}

QLabel#ProjectNumberBadge {
    padding: 1px 4px;
    border-radius: 2px;
    font-size: 10px;
    font-weight: 700;
    color: #e8f6f6;
    background: rgba(9,144,143,0.25);
    border: 1px solid rgba(9,144,143,0.50);
    min-width: 24px;
    max-width: 80px;
    text-align: center;
    letter-spacing: 0.2px;
    white-space: nowrap;
    overflow: hidden;
}

QLabel#ProjectNumberBadge:hover {
    background: rgba(9,144,143,0.30);
    border-color: rgba(9,144,143,0.60);
}

QLabel#ProjectClientLabel {
    color: #c5c5d2;
    font-size: 12px;
}

QLabel#ClientIcon {
    color: rgba(197,197,210,0.85);
    font-size: 10px;
}
```

## MembersView

MembersView relies on inline styles applied within `AvatarBubble` (see `widgets/DataDisplayWidgets/MembersView.py`) and does not currently reference a dedicated QSS file. When recreating it in Designer, copy the inline stylesheet from the `AvatarBubble` constructor or move it into a new QSS for easier tweaking.

## StatusWidget

The status pill (`QLabel#StatusLabel`) is styled via inline `setStyleSheet` calls inside `widgets/DataDisplayWidgets/StatusWidget.py`. No QSS selectors exist yet; consider moving the declaration into a shared QSS file if you need theme-specific variations.

## DatesWidget (`styles/Light/dates.qss`)

```css
QFrame#DueDateContainer {
  background: #ffffff;
  border: 1px solid #e1e4e8;
  border-radius: 2px;
}

QLabel#DateLabel {
  color: #495057;
  font-size: 10px;
  font-weight: 500;
}

QLabel#DateValue {
  color: #495057;
  font-size: 10px;
  font-weight: 600;
}

QLabel#DateValue[overdue="true"] {
  color: #dc3545;
  font-size: 11px;
  font-weight: 600;
}

QLabel#DateValue[due_soon="true"] {
  color: #fd7e14;
  font-size: 11px;
  font-weight: 600;
}
```

## DatesWidget (`styles/Dark/dates.qss`)

```css
QFrame#DueDateContainer {
  border: 1px solid rgba(9,144,143,0.55) !important;
  background: #232b33;
  border-radius: 4px;
  padding: 1px;
}

QLabel#DateLabel,
QLabel#DateValue {
  color: #e2e8f0;
  font-size: 10px;
  font-weight: 600;
}

QLabel#DateValue[overdue="true"] {
  color: #fc8181;
  font-size: 11px;
}

QLabel#DateValue[due_soon="true"] {
  color: #f6ad55;
  font-size: 11px;
}

QFrame#DatesPopup {
  border: 1px solid rgba(9,144,143,0.55) !important;
  background: #232b33;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

QFrame#DatesPopup QLabel#DateLabel {
  color: #a0aec0;
  font-size: 10px;
  font-weight: 500;
}

QFrame#DatesPopup QLabel#DateValue {
  color: #e2e8f0;
  font-size: 11px;
  font-weight: 500;
}
```

Use this document as a quick reference while wiring up the Qt Designer prototype; you can paste the snippets into the form's `styleSheet` property or split them into theme-specific files that mirror the production setup.
