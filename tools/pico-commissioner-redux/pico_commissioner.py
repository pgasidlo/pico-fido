#!/usr/bin/env python3
"""pico-commissioner-redux — PHY configuration tool for pico-fido devices."""

import argparse
import struct
import sys

from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.Exceptions import CardRequestTimeoutException, CardConnectionException

# ── Rescue AID ──────────────────────────────────────────────────────────────
RESCUE_AID = [0xA0, 0x58, 0x3F, 0xC1, 0x9B, 0x7E, 0x4F, 0x21]

# ── TLV Tags ────────────────────────────────────────────────────────────────
PHY_VIDPID = 0x00
PHY_LED_GPIO = 0x04
PHY_LED_BTNESS = 0x05
PHY_OPTS = 0x06
PHY_UP_BTN = 0x08
PHY_USB_PRODUCT = 0x09
PHY_ENABLED_CURVES = 0x0A
PHY_ENABLED_USB_ITF = 0x0B
PHY_LED_DRIVER = 0x0C

TAG_NAMES = {
    PHY_VIDPID: "VID:PID",
    PHY_LED_GPIO: "LED GPIO",
    PHY_LED_BTNESS: "LED Brightness",
    PHY_OPTS: "Options",
    PHY_UP_BTN: "Button Timeout",
    PHY_USB_PRODUCT: "USB Product Name",
    PHY_ENABLED_CURVES: "Enabled Curves",
    PHY_ENABLED_USB_ITF: "Enabled USB Interfaces",
    PHY_LED_DRIVER: "LED Driver",
}

# ── Option flags (PHY_OPTS, uint16 BE) ──────────────────────────────────────
OPT_FLAGS = {
    "wcid": 0x0001,
    "dimmable": 0x0002,
    "no-power-reset": 0x0004,
    "led-steady": 0x0008,
}

# ── Curve flags (PHY_ENABLED_CURVES, uint32 BE) ─────────────────────────────
CURVE_FLAGS = {
    "secp256r1": 0x001,
    "secp384r1": 0x002,
    "secp521r1": 0x004,
    "secp256k1": 0x008,
    "bp256r1": 0x010,
    "bp384r1": 0x020,
    "bp512r1": 0x040,
    "ed25519": 0x080,
    "ed448": 0x100,
    "curve25519": 0x200,
    "curve448": 0x400,
}

# ── USB interface flags (PHY_ENABLED_USB_ITF, uint8) ────────────────────────
USB_ITF_FLAGS = {
    "ccid": 0x1,
    "wcid": 0x2,
    "hid": 0x4,
    "kb": 0x8,
}

# ── LED driver values ───────────────────────────────────────────────────────
LED_DRIVERS = {
    "pico": 0x01,
    "pimoroni": 0x02,
    "ws2812": 0x03,
    "cyw43": 0x04,
    "neopixel": 0x05,
    "none": 0xFF,
}
LED_DRIVER_NAMES = {v: k for k, v in LED_DRIVERS.items()}


# ── APDU Transport ──────────────────────────────────────────────────────────
class APDUError(Exception):
    def __init__(self, sw1, sw2):
        self.sw1 = sw1
        self.sw2 = sw2
        super().__init__(f"APDU error: SW={sw1:02X}{sw2:02X}")


def connect():
    """Connect to the first available smartcard."""
    try:
        cardtype = AnyCardType()
        cardrequest = CardRequest(timeout=10, cardType=cardtype)
        card = cardrequest.waitforcard()
        card.connection.connect()
        return card
    except CardRequestTimeoutException:
        print("Error: No card found. Is the device connected?", file=sys.stderr)
        sys.exit(1)


def send_apdu(card, command, p1, p2, data=None):
    """Send an extended-length APDU and return the response bytes."""
    lc = []
    dataf = []
    if data:
        lc = [0x00] + list(len(data).to_bytes(2, "big"))
        dataf = list(data) if not isinstance(data, list) else data
    le = [0x00, 0x00]

    if isinstance(command, list) and len(command) > 1:
        apdu = list(command)
    else:
        apdu = [0x00, command]

    apdu = apdu + [p1, p2] + lc + dataf + le
    try:
        response, sw1, sw2 = card.connection.transmit(apdu)
    except CardConnectionException:
        card.connection.reconnect()
        response, sw1, sw2 = card.connection.transmit(apdu)
    if sw1 != 0x90:
        raise APDUError(sw1, sw2)
    return response


def select_rescue(card):
    """SELECT the rescue applet."""
    send_apdu(card, 0xA4, 0x04, 0x00, RESCUE_AID)


# ── TLV helpers ─────────────────────────────────────────────────────────────
def parse_tlv(data):
    """Parse a flat TLV stream into a dict of {tag: bytes}."""
    result = {}
    i = 0
    while i + 1 < len(data):
        tag = data[i]
        length = data[i + 1]
        i += 2
        value = bytes(data[i : i + length])
        i += length
        result[tag] = value
    return result


def build_tlv(tag, value):
    """Build a single TLV: [tag, length, value...]."""
    if isinstance(value, int):
        value = [value]
    v = list(value) if not isinstance(value, list) else value
    return [tag, len(v)] + v


# ── Flag helpers ────────────────────────────────────────────────────────────
def flags_to_names(value, flag_map):
    return [name for name, bit in flag_map.items() if value & bit]


def names_to_flags(names, flag_map):
    result = 0
    for name in names:
        key = name.lower()
        if key not in flag_map:
            print(f"Error: Unknown flag '{name}'. Valid: {', '.join(flag_map)}", file=sys.stderr)
            sys.exit(1)
        result |= flag_map[key]
    return result


# ── Display ─────────────────────────────────────────────────────────────────
def format_vidpid(data):
    vid = struct.unpack("<H", data[0:2])[0]
    pid = struct.unpack("<H", data[2:4])[0]
    return f"{vid:04X}:{pid:04X}"


def format_opts(data):
    val = struct.unpack(">H", data)[0]
    names = flags_to_names(val, OPT_FLAGS)
    return f"0x{val:04X} ({', '.join(names) if names else 'none'})"


def format_curves(data):
    val = struct.unpack(">I", data)[0]
    names = flags_to_names(val, CURVE_FLAGS)
    return f"0x{val:08X} ({', '.join(names) if names else 'none'})"


def format_usb_itf(data):
    val = data[0]
    names = flags_to_names(val, USB_ITF_FLAGS)
    return f"0x{val:02X} ({', '.join(names) if names else 'none'})"


def format_led_driver(data):
    val = data[0]
    name = LED_DRIVER_NAMES.get(val, f"unknown(0x{val:02X})")
    return name


def display_phy(tlv):
    """Pretty-print parsed PHY TLV data."""
    print("── PHY Configuration ──")
    for tag, value in sorted(tlv.items()):
        label = TAG_NAMES.get(tag, f"Tag 0x{tag:02X}")
        if tag == PHY_VIDPID:
            formatted = format_vidpid(value)
        elif tag == PHY_OPTS:
            formatted = format_opts(value)
        elif tag == PHY_ENABLED_CURVES:
            formatted = format_curves(value)
        elif tag == PHY_ENABLED_USB_ITF:
            formatted = format_usb_itf(value)
        elif tag == PHY_LED_DRIVER:
            formatted = format_led_driver(value)
        elif tag == PHY_USB_PRODUCT:
            formatted = value.rstrip(b"\x00").decode("utf-8", errors="replace")
        elif tag == PHY_LED_BTNESS:
            formatted = f"{value[0]} (0-15)"
        elif tag == PHY_LED_GPIO:
            formatted = str(value[0])
        elif tag == PHY_UP_BTN:
            formatted = f"{value[0]}s"
        else:
            formatted = value.hex()
        print(f"  {label:.<28s} {formatted}")


# ── Interactive mode ────────────────────────────────────────────────────────
def interactive_write(card):
    """Interactively ask for each PHY option and write."""
    print("── Interactive PHY Configuration ──")
    print("Press Enter to skip (keep current value).\n")

    payload = []

    val = input("VID:PID (e.g. 2E8A:10FE): ").strip()
    if val:
        payload += build_vidpid_tlv(val)

    val = input("LED GPIO pin: ").strip()
    if val:
        payload += build_tlv(PHY_LED_GPIO, int(val))

    val = input(f"LED brightness (0-15): ").strip()
    if val:
        payload += build_tlv(PHY_LED_BTNESS, int(val))

    val = input(f"LED driver ({', '.join(LED_DRIVERS)}): ").strip()
    if val:
        payload += build_tlv(PHY_LED_DRIVER, LED_DRIVERS[val.lower()])

    val = input("Button timeout (seconds): ").strip()
    if val:
        payload += build_tlv(PHY_UP_BTN, int(val))

    val = input("USB product name: ").strip()
    if val:
        payload += build_tlv(PHY_USB_PRODUCT, list(val.encode("utf-8")) + [0x00])

    val = input(f"Options ({', '.join(OPT_FLAGS)}, comma-separated): ").strip()
    if val:
        flags = names_to_flags(val.split(","), OPT_FLAGS)
        payload += build_tlv(PHY_OPTS, list(struct.pack(">H", flags)))

    val = input(f"Curves ({', '.join(CURVE_FLAGS)}, comma-separated): ").strip()
    if val:
        flags = names_to_flags(val.split(","), CURVE_FLAGS)
        payload += build_tlv(PHY_ENABLED_CURVES, list(struct.pack(">I", flags)))

    val = input(f"USB interfaces ({', '.join(USB_ITF_FLAGS)}, comma-separated): ").strip()
    if val:
        flags = names_to_flags(val.split(","), USB_ITF_FLAGS)
        payload += build_tlv(PHY_ENABLED_USB_ITF, flags)

    if not payload:
        print("No changes specified.")
        return

    select_rescue(card)
    send_apdu(card, [0x80, 0x1C], 0x01, 0x00, payload)
    print("\nPHY configuration written successfully.")


# ── TLV builders for CLI args ───────────────────────────────────────────────
def build_vidpid_tlv(vidpid_str):
    parts = vidpid_str.split(":")
    if len(parts) != 2:
        print("Error: VID:PID must be in format XXXX:XXXX", file=sys.stderr)
        sys.exit(1)
    vid = int(parts[0], 16)
    pid = int(parts[1], 16)
    return build_tlv(PHY_VIDPID, list(struct.pack("<HH", vid, pid)))


# ── Commands ────────────────────────────────────────────────────────────────
def cmd_read(args):
    card = connect()
    select_rescue(card)
    response = send_apdu(card, [0x80, 0x1E], 0x01, 0x00)
    tlv = parse_tlv(response)
    display_phy(tlv)


def cmd_write(args):
    card = connect()

    # Check if any arguments were provided
    has_args = any([
        args.vid_pid, args.led_gpio is not None, args.led_brightness is not None,
        args.led_driver, args.button_timeout is not None, args.product_name,
        args.opts, args.curves, args.usb_interfaces,
    ])

    if not has_args:
        interactive_write(card)
        return

    payload = []

    if args.vid_pid:
        payload += build_vidpid_tlv(args.vid_pid)

    if args.led_gpio is not None:
        payload += build_tlv(PHY_LED_GPIO, args.led_gpio)

    if args.led_brightness is not None:
        if not 0 <= args.led_brightness <= 15:
            print("Error: Brightness must be 0-15", file=sys.stderr)
            sys.exit(1)
        payload += build_tlv(PHY_LED_BTNESS, args.led_brightness)

    if args.led_driver:
        driver = args.led_driver.lower()
        if driver not in LED_DRIVERS:
            print(f"Error: Unknown LED driver '{driver}'. Valid: {', '.join(LED_DRIVERS)}", file=sys.stderr)
            sys.exit(1)
        payload += build_tlv(PHY_LED_DRIVER, LED_DRIVERS[driver])

    if args.button_timeout is not None:
        payload += build_tlv(PHY_UP_BTN, args.button_timeout)

    if args.product_name:
        payload += build_tlv(PHY_USB_PRODUCT, list(args.product_name.encode("utf-8")) + [0x00])

    if args.opts:
        flags = names_to_flags(args.opts, OPT_FLAGS)
        payload += build_tlv(PHY_OPTS, list(struct.pack(">H", flags)))

    if args.curves:
        flags = names_to_flags(args.curves, CURVE_FLAGS)
        payload += build_tlv(PHY_ENABLED_CURVES, list(struct.pack(">I", flags)))

    if args.usb_interfaces:
        flags = names_to_flags(args.usb_interfaces, USB_ITF_FLAGS)
        payload += build_tlv(PHY_ENABLED_USB_ITF, flags)

    if not payload:
        print("No changes specified.")
        return

    select_rescue(card)
    send_apdu(card, [0x80, 0x1C], 0x01, 0x00, payload)
    print("PHY configuration written successfully.")

    # Read back and display
    response = send_apdu(card, [0x80, 0x1E], 0x01, 0x00)
    tlv = parse_tlv(response)
    display_phy(tlv)


def cmd_secure_boot(args):
    card = connect()
    select_rescue(card)

    if args.action == "status":
        response = send_apdu(card, [0x80, 0x1E], 0x03, 0x00)
        if len(response) >= 3:
            enabled = "Yes" if response[0] else "No"
            locked = "Yes" if response[1] else "No"
            bootkey = response[2]
            print("── Secure Boot Status ──")
            print(f"  Enabled ............ {enabled}")
            print(f"  Locked ............. {locked}")
            print(f"  Boot Key Slot ...... {bootkey}")
        else:
            print(f"Unexpected response: {bytes(response).hex()}")

    elif args.action == "enable":
        p1 = args.key
        p2 = 0x01 if args.lock else 0x00
        send_apdu(card, [0x80, 0x1D], p1, p2)
        print(f"Secure boot enabled (key slot {p1}, lock={'yes' if args.lock else 'no'}).")


def cmd_reboot(args):
    card = connect()
    select_rescue(card)
    p1 = 0x01 if args.bootsel else 0x00
    try:
        send_apdu(card, [0x80, 0x1F], p1, 0x00)
    except (APDUError, CardConnectionException):
        pass  # Device reboots and disconnects — expected
    mode = "BOOTSEL" if args.bootsel else "normal"
    print(f"Device rebooting ({mode} mode).")


# ── Argument parser ─────────────────────────────────────────────────────────
def build_parser():
    parser = argparse.ArgumentParser(
        prog="pico-commissioner",
        description="PHY configuration tool for pico-fido devices.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # read
    sub.add_parser("read", help="Read current PHY configuration")

    # write
    wp = sub.add_parser("write", help="Write PHY configuration")
    wp.add_argument("--vid-pid", help="USB VID:PID (e.g. 2E8A:10FE)")
    wp.add_argument("--led-gpio", type=int, help="LED GPIO pin number")
    wp.add_argument("--led-brightness", type=int, help="LED brightness (0-15)")
    wp.add_argument("--led-driver", choices=list(LED_DRIVERS), help="LED driver type")
    wp.add_argument("--button-timeout", type=int, help="UP button timeout (seconds)")
    wp.add_argument("--product-name", help="USB product name string")
    wp.add_argument("--opts", nargs="+", metavar="OPT", help=f"Options: {', '.join(OPT_FLAGS)}")
    wp.add_argument("--curves", nargs="+", metavar="CURVE", help=f"Curves: {', '.join(CURVE_FLAGS)}")
    wp.add_argument("--usb-interfaces", nargs="+", metavar="ITF", help=f"Interfaces: {', '.join(USB_ITF_FLAGS)}")

    # secure-boot
    sp = sub.add_parser("secure-boot", help="Manage secure boot")
    ssub = sp.add_subparsers(dest="action", required=True)
    ssub.add_parser("status", help="Read secure boot status")
    ep = ssub.add_parser("enable", help="Enable secure boot")
    ep.add_argument("--key", type=int, default=0, help="Boot key slot (default: 0)")
    ep.add_argument("--lock", action="store_true", help="Lock OTP (irreversible!)")

    # reboot
    rp = sub.add_parser("reboot", help="Reboot device")
    rp.add_argument("--bootsel", action="store_true", help="Reboot into BOOTSEL mode")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "read": cmd_read,
        "write": cmd_write,
        "secure-boot": cmd_secure_boot,
        "reboot": cmd_reboot,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
