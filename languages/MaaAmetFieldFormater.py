"""Helpers for formatting Maa-amet field values."""

from PyQt5.QtCore import QDate

from ..constants.cadastral_fields import Katastriyksus


def default_formatter(value):
    """Convert any value to string."""
    return str(value)


def text_formatter(value):
    """Convert to string, replace underscores with spaces, capitalize."""
    text = str(value).replace("_", " ")
    return text.capitalize()


def date_formatter(value):
    """Format QDate values using the default display format."""
    if isinstance(value, QDate):
        return value.toString("dd.MM.yyyy")
    return value


def date_formatter_for_Kavitro_insertion(value):
    """Format QDate values for Kavitro insertion."""
    if isinstance(value, QDate):
        return value.toString("yyyy-MM-dd")
    return value


def number_formatter(value):
    """Convert numeric values to string."""
    return str(value)


def percentage_formatter(value):
    """Format percentage values as a float with a percent sign."""
    try:
        return f"{float(value)}%"
    except (ValueError, TypeError):
        return str(value)


def area_formatter(value):
    """Format area values as a float with two decimals."""
    try:
        return f"{float(value)}"
    except (ValueError, TypeError):
        return str(value)

FID_FIELD = getattr(Katastriyksus, "fid", "fid")  # Older deployments may lack fid constant

# Mapping field names to their corresponding formatter functions.
formatters = {
    FID_FIELD: default_formatter,                 # Base ID, likely numeric
    Katastriyksus.tunnus: text_formatter,         # Text field
    Katastriyksus.hkood: text_formatter,          # Text field
    #"mk_nimi": text_formatter,        # Region name, text
    #"ov_nimi": text_formatter,        # Municipality name, text
    #"ay_nimi": text_formatter,        # Settlement name, text
    #"l_aadress": text_formatter,      # Address, text
    Katastriyksus.registr: date_formatter,        # Registration date
    Katastriyksus.muudet: date_formatter,         # Last modification date
    Katastriyksus.siht1: text_formatter,          # Text field
    Katastriyksus.siht2: text_formatter,          # Text field
    Katastriyksus.siht3: text_formatter,          # Text field
    Katastriyksus.so_prts1: percentage_formatter, # Percentage field
    Katastriyksus.so_prts2: percentage_formatter, # Percentage field
    Katastriyksus.so_prts3: percentage_formatter, # Percentage field
    Katastriyksus.pindala: area_formatter,        # Area, numeric
    Katastriyksus.haritav: text_formatter,        # Text field
    Katastriyksus.rohumaa: text_formatter,        # Text field
    Katastriyksus.mets: text_formatter,           # Text field
    Katastriyksus.ouemaa: text_formatter,         # Text field
    Katastriyksus.muumaa: text_formatter,         # Text field
    Katastriyksus.kinnistu: text_formatter,       # Plot number, text (or numeric)
    Katastriyksus.omvorm: text_formatter,         # Ownership form, text
    Katastriyksus.maks_hind: number_formatter,    # Maximum price, numeric
    Katastriyksus.marked: text_formatter,         # Text field
    Katastriyksus.eksport: text_formatter         # Text field
}

# A helper function to apply formatting to a field value.
def format_field(field_name, value):
    """
    Returns a formatted value for a given field name.
    If the value is None or a string "NULL" (case insensitive), returns a placeholder.
    """
    if value is None or str(value).upper() == "NULL":
        return "---"
    
    # Retrieve the appropriate formatter; default to default_formatter if not found.
    formatter = formatters.get(field_name, default_formatter)
    return formatter(value)

