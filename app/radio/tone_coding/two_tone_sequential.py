# Two-Tone Sequential (Motorola QuickCall 2)
# 60 tones between 288 - 1433 Hz,
# broken into 6 groups

# tone_a minimum: 1.0 sec
# tone_b minimum: 3.0 sec
# gap/space minumum: 0.7 sec
# total page minimum: 7.0 seconds
#    tone_a + tone_b + space + voice >= 7.0 seconds
from dataclasses import dataclass
import logging
from enum import Enum


logger = logging.getLogger('radio.tone_coding.twotone')

class QuickCall2PagingTypes(Enum):
    INDIVIDUAL_CALL_TONE_AND_VOICE = 0
    GROUP_CALL = 1
    TONE_ONLY = 2
    TONE_ONLY_BATTERY_SAVE = 3

TWOTONE_MIN = 288.5
TWOTONE_MAX = 2468.2
TWOTONE_TONE_1_MIN = 1.0 * 0.85
TWOTONE_TONE_1_MAX = 1.0 * 1.15
TWOTONE_TONE_2_MIN = 3.0 * 0.85
TWOTONE_TONE_2_MAX = 3.0 * 1.15

REED_GROUPS = [1, 2, 3, 4, 5, 6, 10, 11]


@dataclass
class TwoToneDiscreteTone:
    reed_group: int
    tone_num: int
    reed_code: int
    freq: float


@dataclass
class TwoToneSequence:
    group: int
    id: int

    # additional
    tone_1: TwoToneDiscreteTone
    tone_1_diff: float
    tone_2: TwoToneDiscreteTone
    tone_2_diff: float


codes: list[TwoToneDiscreteTone] = [
    TwoToneDiscreteTone(1, 1, 111, 349.0),
    TwoToneDiscreteTone(2, 1, 121, 600.9),
    TwoToneDiscreteTone(3, 1, 138, 288.5),
    TwoToneDiscreteTone(4, 1, 141, 339.6),
    TwoToneDiscreteTone(5, 1, 151, 584.8),
    TwoToneDiscreteTone(6, 1, 191, 1153.4),
    TwoToneDiscreteTone(10, 1, 171, 1513.5),
    TwoToneDiscreteTone(11, 1, 201, 1989.0),
    TwoToneDiscreteTone(1, 2, 112, 368.5),
    TwoToneDiscreteTone(2, 2, 122, 634.5),
    TwoToneDiscreteTone(3, 2, 108, 296.5),
    TwoToneDiscreteTone(4, 2, 142, 358.6),
    TwoToneDiscreteTone(5, 2, 152, 617.4),
    TwoToneDiscreteTone(6, 2, 192, 1185.2),
    TwoToneDiscreteTone(10, 2, 172, 1555.2),
    TwoToneDiscreteTone(11, 2, 202, 2043.8),
    TwoToneDiscreteTone(1, 3, 113, 389.0),
    TwoToneDiscreteTone(2, 3, 123, 669.9),
    TwoToneDiscreteTone(3, 3, 139, 304.7),
    TwoToneDiscreteTone(4, 3, 143, 378.6),
    TwoToneDiscreteTone(5, 3, 153, 651.9),
    TwoToneDiscreteTone(6, 3, 193, 1217.8),
    TwoToneDiscreteTone(10, 3, 173, 1598.0),
    TwoToneDiscreteTone(11, 3, 203, 2094.5),
    TwoToneDiscreteTone(1, 4, 114, 410.8),
    TwoToneDiscreteTone(2, 4, 124, 707.3),
    TwoToneDiscreteTone(3, 4, 109, 313.0),
    TwoToneDiscreteTone(4, 4, 144, 399.8),
    TwoToneDiscreteTone(5, 4, 154, 688.3),
    TwoToneDiscreteTone(6, 4, 194, 1251.4),
    TwoToneDiscreteTone(10, 4, 174, 1642.0),
    TwoToneDiscreteTone(11, 4, 204, 2155.6),
    TwoToneDiscreteTone(1, 5, 115, 433.7),
    TwoToneDiscreteTone(2, 5, 125, 746.8),
    TwoToneDiscreteTone(3, 5, 160, 953.7),
    TwoToneDiscreteTone(4, 5, 145, 422.1),
    TwoToneDiscreteTone(5, 5, 155, 726.8),
    TwoToneDiscreteTone(6, 5, 195, 1285.8),
    TwoToneDiscreteTone(10, 5, 175, 1687.2),
    TwoToneDiscreteTone(11, 5, 205, 2212.2),
    TwoToneDiscreteTone(1, 6, 116, 457.9),
    TwoToneDiscreteTone(2, 6, 126, 788.5),
    TwoToneDiscreteTone(3, 6, 130, 979.9),
    TwoToneDiscreteTone(4, 6, 146, 445.7),
    TwoToneDiscreteTone(5, 6, 156, 767.4),
    TwoToneDiscreteTone(6, 6, 196, 1321.2),
    TwoToneDiscreteTone(10, 6, 176, 1733.7),
    TwoToneDiscreteTone(11, 6, 206, 2271.7),
    TwoToneDiscreteTone(1, 7, 117, 483.5),
    TwoToneDiscreteTone(2, 7, 127, 832.5),
    TwoToneDiscreteTone(3, 7, 161, 1006.9),
    TwoToneDiscreteTone(4, 7, 147, 470.5),
    TwoToneDiscreteTone(5, 7, 157, 810.2),
    TwoToneDiscreteTone(6, 7, 197, 1357.6),
    TwoToneDiscreteTone(10, 7, 177, 1781.5),
    TwoToneDiscreteTone(11, 7, 207, 2334.6),
    TwoToneDiscreteTone(1, 8, 118, 510.5),
    TwoToneDiscreteTone(2, 8, 128, 879.0),
    TwoToneDiscreteTone(3, 8, 131, 1034.7),
    TwoToneDiscreteTone(4, 8, 148, 496.8),
    TwoToneDiscreteTone(5, 8, 158, 855.5),
    TwoToneDiscreteTone(6, 8, 198, 1395.0),
    TwoToneDiscreteTone(10, 8, 178, 1830.5),
    TwoToneDiscreteTone(11, 8, 208, 2401.0),
    TwoToneDiscreteTone(1, 9, 119, 539.0),
    TwoToneDiscreteTone(2, 9, 129, 928.1),
    TwoToneDiscreteTone(3, 9, 162, 1063.2),
    TwoToneDiscreteTone(4, 9, 149, 524.6),
    TwoToneDiscreteTone(5, 9, 159, 903.2),
    TwoToneDiscreteTone(6, 9, 199, 1433.4),
    TwoToneDiscreteTone(10, 9, 179, 1881.0),
    TwoToneDiscreteTone(11, 9, 209, 2468.2),
    TwoToneDiscreteTone(1, 0, 110, 330.5),
    TwoToneDiscreteTone(2, 0, 120, 569.1),
    TwoToneDiscreteTone(3, 0, 189, 1092.4),
    TwoToneDiscreteTone(4, 0, 140, 321.7),
    TwoToneDiscreteTone(5, 0, 150, 553.9),
    TwoToneDiscreteTone(6, 0, 190, 1122.5),
    TwoToneDiscreteTone(10, 0, 170, 1472.9),
    TwoToneDiscreteTone(11, 0, 200, 1930.2)
]

grouped_codes: dict[int, list[TwoToneDiscreteTone]] = {}
for group in REED_GROUPS:
    grouped_codes[group] = {}
for code in codes:
    grouped_codes[code.reed_group][code.tone_num] = code

# Find the pair of frequencies which most closely fit the supplied
# tone frequencies from the same Reed Group
def code_from_freqs(tone_a: float, tone_b: float) -> TwoToneSequence:

    if not isinstance(tone_a, float) or not isinstance(tone_b, float):
        raise ValueError("tone_a and tone_b must be float!")

    tol = 60.  # temporary placeholder
    if tone_a > (TWOTONE_MAX + tol) or tone_a < (TWOTONE_MIN - tol):
        raise ValueError(f"tone A ({tone_a}) is out of spec for Quick Call 2!")
    if tone_b > (TWOTONE_MAX + tol) or tone_b < (TWOTONE_MIN - tol):
        raise ValueError(f"tone B ({tone_b}) is out of spec for Quick Call 2!")

    matches = {}

    # match closest code for each group first
    for group in REED_GROUPS:

        matches[group] = {}

        matches[group]['dist_a'] = None
        matches[group]['code_a'] = None

        matches[group]['dist_b'] = None
        matches[group]['code_b'] = None

        for code in grouped_codes[group].values():

            dist_a = abs(tone_a - code.freq)
            if matches[group]['dist_a'] is None or dist_a < matches[group]['dist_a']:
                matches[group]['dist_a'] = dist_a
                matches[group]['code_a'] = code

            dist_b = abs(tone_b - code.freq)
            if matches[group]['dist_b'] is None or dist_a < matches[group]['dist_b']:
                matches[group]['dist_b'] = dist_b
                matches[group]['code_b'] = code


    # smallest sum?
    closest_sum_dist = matches[REED_GROUPS[0]]['dist_a']
    closest_sum_group = REED_GROUPS[0]

    for group, match in matches.items():

        code_a: TwoToneDiscreteTone = match['code_a']
        code_b: TwoToneDiscreteTone = match['code_b']
        dist_a = match['dist_a']
        dist_b = match['dist_b']

        if (dist_a + dist_b) < closest_sum_dist:
            closest_sum_dist = dist_a + dist_b
            closest_sum_group = group

        # print(f"{group:>5} {code_a.reed_code} {code_a.freq} d={round(dist_a,1)} ")
        # print(f"      {code_b.reed_code} {code_b.freq} d={round(dist_b,1)}")

    # Check closest match
    code_a = matches[closest_sum_group]['code_a']
    code_b = matches[closest_sum_group]['code_b']
    dist_a = round(abs(code_a.freq - tone_a), 1)
    dist_b = round(abs(code_b.freq - tone_b), 1)

    closest_match = TwoToneSequence(
        group=closest_sum_group,
        id=int(code_a.tone_num) * 10 + int(code_b.tone_num),
        tone_1=code_a,tone_2=code_b,
        tone_1_diff=dist_a, tone_2_diff=dist_b
    )

    min_spacing_group = min(freq_spacing_grouped[closest_match.group])

    if (dist_a > min_spacing_group / 2):
        logger.warning(f"tone_a is {round(dist_a,1)} from center")

    if (dist_b > min_spacing_group / 2):
        logger.warning(f"tone B is {round(dist_b, 1)} from center")

    return closest_match

# Frequency spacings for all sorted frequencies (288.5 throuh 2468.2 Hz)
freq_spacing_all = [
    8.0, 8.2, 8.3, 8.7, 8.8, 9.1, 9.4, 9.6, 9.9, 10.1, 10.4, 10.8, 11.0,
    11.3, 11.6, 12.0, 12.2, 12.6, 13.0, 13.3, 13.7, 14.1, 14.4, 14.9, 15.2,
    15.7, 16.1, 16.5, 17.1, 17.4, 18.0, 18.4, 19.0, 19.5, 20.0, 20.6, 21.1,
    21.7, 22.3, 23.0, 23.5, 24.2, 24.9, 25.6, 26.2, 27.0, 27.8, 28.5, 29.2,
    30.1, 30.9, 31.8, 32.6, 33.6, 34.4, 35.4, 36.4, 37.4, 38.4, 39.5, 40.6,
    41.7, 42.8, 44.0, 45.2, 46.5, 47.8, 49.0, 50.5, 49.2, 58.8, 54.8, 50.7,
    61.1, 56.6, 59.5, 62.9, 66.4, 67.2
]

# Frequencies grouped by Reed Code
freq_spacing_grouped = {
    1: [18.5, 19.5, 20.5, 21.8, 22.9, 24.2, 25.6, 27.0, 28.5],
    2: [31.8, 33.6, 35.4, 37.4, 39.5, 41.7, 44.0, 46.5, 49.1],
    3: [8.0, 8.2, 8.3, 640.7, 26.2, 27.0, 27.8, 28.5, 29.2],
    4: [17.9, 19.0, 20.0, 21.2, 22.3, 23.6, 24.8, 26.3, 27.8],
    5: [30.9, 32.6, 34.5, 36.4, 38.5, 40.6, 42.8, 45.3, 47.7],
    6: [30.9, 31.8, 32.6, 33.6, 34.4, 35.4, 36.4, 37.4, 38.4],
    10: [40.6, 41.7, 42.8, 44.0, 45.2, 46.5, 47.8, 49.0, 50.5],
    11: [58.8, 54.8, 50.7, 61.1, 56.6, 59.5, 62.9, 66.4, 67.2]
}

table = """
1 111 349.0 121 600.9 138 288.5 141 339.6 151 584.8 191 1153.4 171 1513.5 201 1989.0
2 112 368.5 122 634.5 108 296.5 142 358.6 152 617.4 192 1185.2 172 1555.2 202 2043.8
3 113 389.0 123 669.9 139 304.7 143 378.6 153 651.9 193 1217.8 173 1598.0 203 2094.5
4 114 410.8 124 707.3 109 313.0 144 399.8 154 688.3 194 1251.4 174 1642.0 204 2155.6
5 115 433.7 125 746.8 160 953.7 145 422.1 155 726.8 195 1285.8 175 1687.2 205 2212.2
6 116 457.9 126 788.5 130 979.9 146 445.7 156 767.4 196 1321.2 176 1733.7 206 2271.7
7 117 483.5 127 832.5 161 1006.9 147 470.5 157 810.2 197 1357.6 177 1781.5 207 2334.6
8 118 510.5 128 879.0 131 1034.7 148 496.8 158 855.5 198 1395.0 178 1830.5 208 2401.0
9 119 539.0 129 928.1 162 1063.2 149 524.6 159 903.2 199 1433.4 179 1881.0 209 2468.2
0 110 330.5 120 569.1 189 1092.4 140 321.7 150 553.9 190 1122.5 170 1472.9 200 1930.2
"""

def convert_table(table: str) -> list[TwoToneDiscreteTone]:

    codes: list[TwoToneDiscreteTone] = []

    for line in table.splitlines():
        if len(line) == 0:
            continue  # skip blank lines

        tone_no = int(line[0])
        row = line[2:]
        parts = row.split(" ")

        for i in range(8):
            codes.append(TwoToneDiscreteTone(
                reed_group = REED_GROUPS[i],
                tone_num=tone_no,
                reed_code=parts[i*2],
                freq=float(parts[i*2+1])
            ))

    return codes



if __name__ == "__main__":

    logging.basicConfig()

    tone_a = 672
    tone_b = 641

    code = code_from_freqs(tone_a, tone_b)

