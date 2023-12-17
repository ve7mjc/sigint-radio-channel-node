
designators: list[str] = [
    '10K1F3E',
    '11K2F3E',
    '12K5F2E'
]

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

# @dataclass

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