# Tenstar RP2350-USB — Pico FIDO Setup

Guide for configuring the Tenstar RP2350-USB board with pico-fido firmware as a FIDO2/SSH security key.

## Board Specifications

| Parameter | Value |
|-----------|-------|
| Chip | RP2350A (dual-core) |
| Flash | 16 MB |
| USB | USB-A male |
| LED | WS2812 RGB on GP22 |
| Button | BOOTSEL (QSPI CS) |
| PICO_BOARD | `pico2` |

## Requirements

- `opensc-tool` (`opensc` package)
- `pcscd` (`pcsc-lite` package)
- OpenSSH 8.2+ (FIDO2 key support)
- pico-fido firmware flashed to the board

## 1. CCID Configuration (Info.plist)

The CCID driver needs to know the device VID/PID. Add the Raspberry Pi identifiers to the configuration file:

**File:** `/usr/lib/pcsc/drivers/ifd-ccid.bundle/Contents/Info.plist`

Add entries at the first position in three arrays (`ifdVendorID`, `ifdProductID`, `ifdFriendlyName`):

```xml
<key>ifdVendorID</key>
<array>
    <string>0x2E8A</string>
    <!-- rest of entries... -->

<key>ifdProductID</key>
<array>
    <string>0x10FE</string>
    <!-- rest of entries... -->

<key>ifdFriendlyName</key>
<array>
    <string>Pico Key</string>
    <!-- rest of entries... -->
```

Restart the service after editing:

```bash
sudo systemctl restart pcscd
```

Verify — the device should be visible:

```
$ opensc-tool -l
# Detected readers (pcsc)
Nr.  Card  Features  Name
0    Yes             Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00
1    No              Broadcom Corp 58200 [Contacted SmartCard] (0123456789ABCD) 01 00
2    No              Broadcom Corp 58200 [Contactless SmartCard] (0123456789ABCD) 02 00
```

## 2. PHY Configuration (LED + Button)

SELECT rescue applet and write PHY can be done in a single command:

```
$ opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 09 0401160C010308010F"
Using reader with a card: Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00
Sending: 00 A4 04 00 08 A0 58 3F C1 9B 7E 4F 21
Received (SW1=0x90, SW2=0x00):
01 02 07 04 8D 94 99 7D 95 77 EE 53 .......}.w.S
Sending: 80 1C 01 00 09 04 01 16 0C 01 03 08 01 0F
Received (SW1=0x90, SW2=0x00)
```

Rescue applet AID: `A0 58 3F C1 9B 7E 4F 21`

### APDU Command Structure

| Byte | Value | Description |
|------|-------|-------------|
| CLA | `0x80` | Proprietary class (not `0x00` — returns `6E00`) |
| INS | `0x1C` | WRITE |
| P1 | `0x01` | PHY data |
| P2 | `0x00` | — |
| Lc | `0x09` | Payload length (9 bytes) |

### Payload Structure (TLV)

| Tag | Length | Value | Description |
|-----|--------|-------|-------------|
| `0x04` | `0x01` | `0x16` (22) | LED GPIO — GP22 |
| `0x0C` | `0x01` | `0x03` | LED driver — WS2812 |
| `0x08` | `0x01` | `0x0F` (15) | Button timeout — 15 seconds |

## 3. Verification

```
$ opensc-tool -l
# Detected readers (pcsc)
Nr.  Card  Features  Name
0    Yes             Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00

$ opensc-tool -s "00A40400 08 A0583FC19B7E4F21"
Using reader with a card: Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00
Sending: 00 A4 04 00 08 A0 58 3F C1 9B 7E 4F 21
Received (SW1=0x90, SW2=0x00):
01 02 07 04 8D 94 99 7D 95 77 EE 53 .......}.w.S
```

After successful configuration:
- WS2812 LED lights up during cryptographic operations
- BOOTSEL requires a 15-second press for authorization

## 4. SSH Configuration with FIDO2 Key

### Generate a resident Ed25519-SK key

```bash
ssh-keygen -t ed25519-sk -O resident -O verify-required -C "pico-fido"
```

A resident key is stored on the device — it can be retrieved on any computer.

### Alternative — ECDSA-SK

```bash
ssh-keygen -t ecdsa-sk -C "pico-fido"
```

### Copy the public key to the server

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_sk.pub user@server
```

### Usage

```bash
ssh -i ~/.ssh/id_ed25519_sk user@server
```

During login, the device will prompt for confirmation via the button (BOOTSEL).

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `SW1=0x6E` | Wrong CLA byte (`0x00`) | Use CLA `0x80` |
| LED not lighting | Default GPIO 25 instead of 22 | Configure PHY_LED_GPIO=22 |
| Button not responding | Timeout=0 (default) | Set PHY_UP_BTN to 15 |
| Device not visible | Missing VID/PID in Info.plist | Add `2E8A:10FE` and restart pcscd |
