"""

Reference: Industry Canada [TRC-43] Designation of Emissions, Class of Station and Nature of Service
           Issue 3, November 2012
https://ised-isde.canada.ca/site/spectrum-management-telecommunications/sites/default/files/attachments/2022/TRC-43-Nov2012-English.pdf


"""


from typing import Union

# Legacy Designators (3 chars)
#   - 1st = modulation_type
#   - 2nd = type of data (eg. voice, telephony)
#
# "Modern" Designators
#
# [1,2,3,4] Necessary Bandwidth
#
# [5] - modulation_type:
#    A - AM
#    F - FM
#
# [6] - Data Content
#    N - None
#    A - Aural telegraphy, for people (Morse code)
#    B - Telegraphy for machine copy (RTTY, fast Morse)
#    C - Analog fax
#    D - Data, telemetry, telecommand
#    E - Telephony, voice, sound broadcasting
#    F - Video, television
#    W - Combinations of the above
#    X - All cases not covered above
#
# [7] - [Not used by FCC]
#
# [8] - Multiplex type [Not used by FCC?]
#    N   None
#    C   Code division
#    F   Frequency division
#    T   Time division
#    W   Combination of above
#    X   All other types

common_designators: dict[str, str] = {
    '16K0F3E': '4 kHz FM analog voice; VHF marine, VHF/UHF ham radio',
    '11K3F3E': '2.5 kHz FM "narrowband" analog voice',
    '11K0F3E': 'FM Narrow LMR, GMRS, FRS, MURS, etc.',
    # '8K40F1E': 'P25 Voice - P25 Phase I C4FM voice',
    # '8K40F1D': 'P25 Project 25 Voice - P25 Phase I C4FM data',
    # '8K30F1W': 'P25 Project 25 Voice and data Phase I C4FM voice and data ',
    # '8K10F1E': 'P25 Project 25 Voice - P25 Phase I C4FM voice ',
    # '8K10F1D': 'P25 Project 25 Data - P25 Phase I C4FM voice',
    # '8K10FXE': '',
    # '8K10FXD': '',
    # '8K30F1D': 'NDXN, IDAS or NEXEDGE Wideband 12.5 kHz - Data',
    # '8K30F1E': 'NDXN, IDAS or NEXEDGE Wideband 12.5 kHz - Digital voice',
    # '8K30F7W': 'NXDN, IDAS or NEXEDGE Wideband 12.5 kHz - Digital voice + data combined',
    # '8K30F1W': 'NXDN, IDAS or NEXEDGE Wideband 12.5 kHz - Digital voice + data combined',
}

# Typical Emissions Designators
# 6K00A3E Double-Sideband Full AM for Aeronautical
# 8K10F1E P25 Phase 1 Voice
# 8K10F1D P25 Phase 1 Data
# 8K30F1W P25 Phase 1 Data+Voice
# 11K0F3E 2.5 kHz Analog FM Voice
# 16K0F3E 5.0 kHz Analog FM Voice (Wide / Marine VHF)

from dataclasses import dataclass

@dataclass
class Designator:
    code: str
    bandwidth: int
    modulation_type: str
    modulation_type_descr: str

    def signal_type_str(self) -> str:
        pass


multipliers: dict[str, int] = {
    'H': 1,
    'K': int(1e3),
    'M': int(1e6),
    'G': int(1e9)
}

modulation_type_codes: dict[str, str] = {
    "N": "None",
    "A": "AM (Amplitude Modulation), double sideband, full carrier",
    "H": "AM, single sideband, full carrier",
    "R": "AM, single sideband, reduced or controlled carrier",
    "J": "AM, single sideband, suppressed carrier",
    "B": "AM, independent sidebands",
    "C": "AM, vestigial sideband  (commonly analog TV)",
    "F": "Angle-modulated, straight FM",
    "G": "Angle-modulated, phase modulation (common; sounds like FM)",
    "D": "Carrier is amplitude and angle modulated",
    "P": "Pulse, no modulation",
    "K": "Pulse, amplitude modulation (PAM, PSM)",
    "L": "Pulse, width modulation (PWM)",
    "M": "Pulse, phase or position modulation (PPM)",
    "Q": "Pulse, carrier also angle-modulated during pulse",
    "W": "Pulse, two or more modes used"
}

def bandwidth_from_designator(designator: str) -> int:
    if len(designator) < 4:
        raise ValueError("designator must be >= 4 characters")
    for code, value in multipliers.items():
        if code in designator:
            return int(float(designator[:4].replace(code,".")) * value)
    raise ValueError("could not determine bandwidth from designator")

def decode_emissions_designator(designator: str) -> Designator:
    if len(designator) < 6 or len(designator) > 8:
        raise ValueError(f"unexpected designator length ({len(designator)})!")

    bandwidth = bandwidth_from_designator(designator)

    # Modulation Type
    modulation_type_code = designator[4]
    if modulation_type_code not in modulation_type_codes:
        raise ValueError(f"unexpected modulation type code '{modulation_type_code}'")

    return Designator(
        code=designator,
        bandwidth=bandwidth,
        modulation_type=modulation_type_code,
        modulation_type_descr=modulation_type_codes[modulation_type_code]
    )

def verbose_designator_dict(designator: Union[str, Designator]) -> str:
    # permit passing of a string designator
    if isinstance(designator, str):
        designator = decode_emissions_designator(designator)

    d = {}
    d['bandwidth'] = designator.bandwidth
    d['modulation_type'] = designator.modulation_type_descr
