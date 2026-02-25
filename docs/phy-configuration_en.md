# PHY Configuration — Pico FIDO

Complete documentation of physical configuration (PHY) options for pico-fido firmware.

## APDU Commands

### Rescue Applet

AID: `A0 58 3F C1 9B 7E 4F 21`

```
$ opensc-tool -s "00A40400 08 A0583FC19B7E4F21"
Using reader with a card: Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00
Sending: 00 A4 04 00 08 A0 58 3F C1 9B 7E 4F 21
Received (SW1=0x90, SW2=0x00):
01 02 07 04 8D 94 99 7D 95 77 EE 53 .......}.w.S
```

### Write PHY

```
CLA: 0x80    (proprietary — NOT 0x00, which returns 6E00)
INS: 0x1C    (WRITE)
P1:  0x01    (PHY data)
P2:  0x00
Lc:  payload length (max 78 bytes)
Data: TLV payload
```

### Read PHY

```
CLA: 0x80
INS: 0x1E    (READ)
P1:  0x01    (PHY data)
P2:  0x00
```

### Secure Boot — read status

```
CLA: 0x80
INS: 0x1E    (READ)
P1:  0x03    (OTP Secure Boot)
P2:  0x00
```

Response: `[boot_enabled, boot_locked, key_number]`

### Secure Boot — enable

```
CLA: 0x80
INS: 0x1D    (SECURE)
P1:  0x00-0x03  (boot key number)
P2:  0x00=no lock, 0x01=lock
```

Requires WebUSB (not WebAuthn).

## TLV Format

PHY payload uses Tag-Length-Value encoding:

```
[Tag: 1 byte] [Length: 1 byte] [Value: Length bytes]
```

Multiple TLVs can be concatenated in a single payload.

## PHY Tags

| Tag | Name | Size | Description |
|-----|------|------|-------------|
| `0x00` | PHY_VIDPID | 4B | USB VID (2B) + PID (2B) |
| `0x04` | PHY_LED_GPIO | 1B | LED GPIO pin number |
| `0x05` | PHY_LED_BTNESS | 1B | LED brightness (0–15) |
| `0x06` | PHY_OPTS | 2B | Option flags (bitfield) |
| `0x08` | PHY_UP_BTN | 1B | Button timeout (seconds, 0=disabled) |
| `0x09` | PHY_USB_PRODUCT | max 32B | USB product name (string) |
| `0x0A` | PHY_ENABLED_CURVES | 4B | Allowed curves (bitfield) |
| `0x0B` | PHY_ENABLED_USB_ITF | 1B | USB interfaces (bitfield) |
| `0x0C` | PHY_LED_DRIVER | 1B | LED driver type |

## LED Drivers (tag 0x0C)

| Value | Name | Platform |
|-------|------|----------|
| `0x01` | Pico (GPIO) | RP2040/RP2350 |
| `0x02` | Pimoroni | All |
| `0x03` | WS2812 | All |
| `0x04` | CYW43 | RP2350 |
| `0x05` | NeoPixel | ESP32 |
| `0xFF` | None | All |

## Option Flags (tag 0x06)

16-bit field, OR-combined flags:

| Bit | Name | Description |
|-----|------|-------------|
| `0x01` | PHY_OPT_WCID | Known vendor (vs Custom VID:PID) |
| `0x02` | PHY_OPT_DIMM | LED dimmable |
| `0x04` | PHY_OPT_DISABLE_POWER_RESET | Disable power cycle on reset |
| `0x08` | PHY_OPT_LED_STEADY | LED steady (no blinking) |

## Cryptographic Curves (tag 0x0A)

32-bit field, OR-combined flags:

| Bit | Curve |
|-----|-------|
| `0x001` | secp256r1 (NIST P-256) |
| `0x002` | secp384r1 (NIST P-384) |
| `0x004` | secp521r1 (NIST P-521) |
| `0x008` | secp256k1 (Bitcoin/Ethereum) |
| `0x010` | brainpoolP256r1 |
| `0x020` | brainpoolP384r1 |
| `0x040` | brainpoolP512r1 |
| `0x080` | Ed25519 |
| `0x100` | Ed448 |
| `0x200` | Curve25519 (X25519) |
| `0x400` | Curve448 (X448) |

Note: Android does not support the secp256k1 curve.

## USB Interfaces (tag 0x0B)

| Bit | Name | Description |
|-----|------|-------------|
| `0x01` | CCID | Smart Card |
| `0x02` | WCID | Web Interface |
| `0x04` | HID | FIDO (U2F/FIDO2) |
| `0x08` | KB | Keyboard (OTP) |

Default: `0x0F` (all enabled).

## Examples

### Basic configuration (LED + button)

WS2812 LED on GP22, button timeout 15s:

```
$ opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 09 0401160C010308010F"
Using reader with a card: Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00
Sending: 00 A4 04 00 08 A0 58 3F C1 9B 7E 4F 21
Received (SW1=0x90, SW2=0x00):
01 02 07 04 8D 94 99 7D 95 77 EE 53 .......}.w.S
Sending: 80 1C 01 00 09 04 01 16 0C 01 03 08 01 0F
Received (SW1=0x90, SW2=0x00)
```

Payload breakdown: `04 01 16` + `0C 01 03` + `08 01 0F`

| Tag | Length | Value | Meaning |
|-----|--------|-------|---------|
| `04` | `01` | `16` (22) | LED GPIO = GP22 |
| `0C` | `01` | `03` | LED driver = WS2812 |
| `08` | `01` | `0F` (15) | Timeout = 15s |

### Change LED brightness

Brightness 10 (out of 15):

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 03 05010A"
```

Payload: `05 01 0A` → PHY_LED_BTNESS = 10

### Set product name

Name "My FIDO Key":

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 0D 09 0B 4D79204649444F204B6579"
```

Payload: `09 0B 4D79204649444F204B6579` → PHY_USB_PRODUCT = "My FIDO Key"

### Custom VID:PID

VID=0x2E8A, PID=0x10FE:

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 06 00 04 2E8A10FE"
```

Payload: `00 04 2E8A10FE` → PHY_VIDPID = 2E8A:10FE

### Enable options (LED dimmable + LED steady)

Flags: `0x02 | 0x08 = 0x000A`

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 04 06 02 000A"
```

Payload: `06 02 000A` → PHY_OPTS = DIMM + STEADY

### Enable secp256k1 curve

Flags: `0x08` (secp256k1 only):

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 06 0A 04 00000008"
```

Payload: `0A 04 00000008` → PHY_ENABLED_CURVES = secp256k1

### Read current PHY configuration

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801E0100"
```

### Read Secure Boot status

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801E0300"
```

### Enable Secure Boot (key 0, no lock)

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801D0000"
```

### Enable Secure Boot with lock (key 0)

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801D0001"
```

**Warning:** Secure Boot with lock is irreversible. Requires WebUSB.
