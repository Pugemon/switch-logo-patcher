#!/usr/bin/env python3

import argparse
import io
import os
from pathlib import Path

import ips
from PIL import Image

LOGO_WIDTH = 308
LOGO_HEIGHT = 350

# Build Id: offset
patch_info = {
    # FW <= 4.0
    # AM Sysmodule https://switchbrew.org/wiki/Applet_Manager_services patches
    "C79F22F18169FCD3B3698A881394F6240385CDB1": 1668164,
    "01890C643E9D6E17B2CDA77A9749ECB9A4F676D6": 1962240,
    "C088ADC91417EBAE6ADBDF3E47946858CAFE1A82": 1962240,
    "3EC573CB22744A993DFE281701E9CBFE66C03ABD": 1716480,
    # FW > 4.0
    # Vi Sysmodule https://switchbrew.org/wiki/Display_services patches
    "7B4123290DE2A6F52DE4AB72BEA1A83D11214C71": 1831168,
    "723DF02F6955D903DF7134105A16D48F06012DB1": 1835264,
    "967F4C3DFC7B165E4F7981373EC1798ACA234A45": 1573120,
    "98446A07BC664573F1578F3745C928D05AB73349": 1589504,
    "0767302E1881700608344A3859BC57013150A375": 1593600,
    "7C5894688EDA24907BC9CE7013630F365B366E4A": 1593600,
    "7421EC6021AC73DD60A635BC2B3AD6FCAE2A6481": 1536256,
    "96529C3226BEE906EE651754C33FE3E24ECAE832": 1544448,  # FW 10.0.0
    "D689E9FAE7CAA4EC30B0CD9B419779F73ED3F88B": 1655040,  # FW 11.0.0
    "65A23B52FCF971400CAA4198656D73867D7F1F1D": 1655040,  # FW 11.0.1
    "B295D3A8F8ACF88CB0C5CE7C0488CC5511B9C389": 1696000,  # FW 12.0.0
    "82EE58BEAB54C1A9D4B3D9ED414E84E31502FAC6": 1708288,  # FW 13.0.0
    "AFEAACF3E88AB539574689D1458060657E81E088": 1716480,  # FW 14.0.0
    "7E9BB552AAEFF82363D1E8C97B5C6B95E3989E1A": 1704192,  # FW 15.0.0
    "BA15B407573B8CECF0FAE2B367D3103A2A1E821C": 2191616,  # FW 16.0.0
}

human_readble_to_build_id = {
    "10.0.0": "96529C3226BEE906EE651754C33FE3E24ECAE832",
    "11.0.0": "D689E9FAE7CAA4EC30B0CD9B419779F73ED3F88B",
    "11.0.1": "65A23B52FCF971400CAA4198656D73867D7F1F1D",
    "12.0.0": "B295D3A8F8ACF88CB0C5CE7C0488CC5511B9C389",
    "13.0.0": "82EE58BEAB54C1A9D4B3D9ED414E84E31502FAC6",
    "14.0.0": "AFEAACF3E88AB539574689D1458060657E81E088",
    "15.0.0": "7E9BB552AAEFF82363D1E8C97B5C6B95E3989E1A",
    "16.0.0": "BA15B407573B8CECF0FAE2B367D3103A2A1E821C",
}
# TODO Fill vales


def create_logo_patch(new_logo_path):
    new_logo = Image.open(new_logo_path).convert("RGBA")
    if new_logo.size != (LOGO_WIDTH, LOGO_HEIGHT):
        raise ValueError("Invalid size for the logo")

    new_f = io.BytesIO(new_logo.tobytes())
    new_f.seek(0, 2)
    new_len = new_f.tell()
    new_f.seek(0)

    logo_patch = ips.Patch()
    while new_f.tell() < new_len:
        logo_patch.add_record(new_f.tell(), new_f.read(0xFFFF))
    return logo_patch


def apply_patch(old_logo_path, new_logo_path):
    old_logo = Image.open(old_logo_path).convert("RGBA")
    new_logo = Image.open(new_logo_path).convert("RGBA")
    if old_logo.size != (LOGO_WIDTH, LOGO_HEIGHT) or new_logo.size != (
        LOGO_WIDTH,
        LOGO_HEIGHT,
    ):
        raise ValueError("Invalid size for the logo")

    return ips.Patch.create(old_logo.tobytes(), new_logo.tobytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "patches_dir",
        help="The directory where the generated patches will be dumped",
        type=Path,
    )
    parser.add_argument("new_logo", help="The new logo image", type=Path)
    parser.add_argument(
        "-o", "--old_logo", help="The original logo image", type=Path, default=None
    )
    parser.add_argument(
        "--fw_version",
        help="The firmware version for which to create the patch",
        choices=human_readble_to_build_id.keys(),
    )

    args = parser.parse_args()

    if args.fw_version:
        ver_build_id = human_readble_to_build_id.get(args.fw_version)
        todo_to_patch = {ver_build_id : patch_info.get(args.fw_version)}
    else:
        todo_to_patch = patch_info

    if args.old_logo is None:
        base_patch = create_logo_patch(args.new_logo)
    else:
        base_patch = apply_patch(args.old_logo, args.new_logo)

    if not args.patches_dir.exists():
        args.patches_dir.mkdir(parents=True)

    for build_id, offset in todo_to_patch.items():
        tmp_p = ips.Patch()

        for r in base_patch.records:
            tmp_p.add_record(r.offset + offset, r.content, r.rle_size)

        with args.patches_dir.joinpath(f"{build_id}.ips").open("wb") as f:
            f.write(bytes(tmp_p))


if __name__ == "__main__":
    main()
