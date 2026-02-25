# Konfiguracja PHY — Pico FIDO

Kompletna dokumentacja opcji fizycznej konfiguracji (PHY) firmware pico-fido.

## Komendy APDU

### Rescue Applet

AID: `A0 58 3F C1 9B 7E 4F 21`

```
$ opensc-tool -s "00A40400 08 A0583FC19B7E4F21"
Using reader with a card: Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00
Sending: 00 A4 04 00 08 A0 58 3F C1 9B 7E 4F 21
Received (SW1=0x90, SW2=0x00):
01 02 07 04 8D 94 99 7D 95 77 EE 53 .......}.w.S
```

### Zapis PHY (WRITE)

```
CLA: 0x80    (proprietary — NIE 0x00, zwróci 6E00)
INS: 0x1C    (WRITE)
P1:  0x01    (PHY data)
P2:  0x00
Lc:  długość payload (max 78 bajtów)
Data: TLV payload
```

### Odczyt PHY (READ)

```
CLA: 0x80
INS: 0x1E    (READ)
P1:  0x01    (PHY data)
P2:  0x00
```

### Secure Boot — odczyt statusu

```
CLA: 0x80
INS: 0x1E    (READ)
P1:  0x03    (OTP Secure Boot)
P2:  0x00
```

Odpowiedź: `[boot_enabled, boot_locked, key_number]`

### Secure Boot — włączenie

```
CLA: 0x80
INS: 0x1D    (SECURE)
P1:  0x00-0x03  (numer klucza boot)
P2:  0x00=bez blokady, 0x01=zablokuj
```

Wymaga WebUSB (nie WebAuthn).

## Format TLV

Payload PHY używa kodowania Tag-Length-Value:

```
[Tag: 1 bajt] [Length: 1 bajt] [Value: Length bajtów]
```

Wiele TLV można łączyć w jednym payload.

## Tagi PHY

| Tag | Nazwa | Rozmiar | Opis |
|-----|-------|---------|------|
| `0x00` | PHY_VIDPID | 4B | USB VID (2B) + PID (2B) |
| `0x04` | PHY_LED_GPIO | 1B | Numer pinu GPIO dla LED |
| `0x05` | PHY_LED_BTNESS | 1B | Jasność LED (0–15) |
| `0x06` | PHY_OPTS | 2B | Flagi opcji (bitfield) |
| `0x08` | PHY_UP_BTN | 1B | Timeout przycisku (sekundy, 0=wyłączony) |
| `0x09` | PHY_USB_PRODUCT | max 32B | Nazwa produktu USB (string) |
| `0x0A` | PHY_ENABLED_CURVES | 4B | Dozwolone krzywe (bitfield) |
| `0x0B` | PHY_ENABLED_USB_ITF | 1B | Interfejsy USB (bitfield) |
| `0x0C` | PHY_LED_DRIVER | 1B | Typ sterownika LED |

## Sterowniki LED (tag 0x0C)

| Wartość | Nazwa | Platforma |
|---------|-------|-----------|
| `0x01` | Pico (GPIO) | RP2040/RP2350 |
| `0x02` | Pimoroni | Wszystkie |
| `0x03` | WS2812 | Wszystkie |
| `0x04` | CYW43 | RP2350 |
| `0x05` | NeoPixel | ESP32 |
| `0xFF` | Brak | Wszystkie |

## Flagi opcji (tag 0x06)

Pole 16-bitowe, kombinacja flag OR:

| Bit | Nazwa | Opis |
|-----|-------|------|
| `0x01` | PHY_OPT_WCID | Znany producent (vs Custom VID:PID) |
| `0x02` | PHY_OPT_DIMM | LED ściemniany |
| `0x04` | PHY_OPT_DISABLE_POWER_RESET | Wyłącz power cycle przy resecie |
| `0x08` | PHY_OPT_LED_STEADY | LED ciągły (bez migania) |

## Krzywe kryptograficzne (tag 0x0A)

Pole 32-bitowe, kombinacja flag OR:

| Bit | Krzywa |
|-----|--------|
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

Uwaga: Android nie obsługuje krzywej secp256k1.

## Interfejsy USB (tag 0x0B)

| Bit | Nazwa | Opis |
|-----|-------|------|
| `0x01` | CCID | Smart Card |
| `0x02` | WCID | Web Interface |
| `0x04` | HID | FIDO (U2F/FIDO2) |
| `0x08` | KB | Klawiatura (OTP) |

Domyślnie: `0x0F` (wszystkie włączone).

## Przykłady

### Podstawowa konfiguracja (LED + przycisk)

LED WS2812 na GP22, timeout przycisku 15s:

```
$ opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 09 0401160C010308010F"
Using reader with a card: Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00
Sending: 00 A4 04 00 08 A0 58 3F C1 9B 7E 4F 21
Received (SW1=0x90, SW2=0x00):
01 02 07 04 8D 94 99 7D 95 77 EE 53 .......}.w.S
Sending: 80 1C 01 00 09 04 01 16 0C 01 03 08 01 0F
Received (SW1=0x90, SW2=0x00)
```

Rozkład payload: `04 01 16` + `0C 01 03` + `08 01 0F`

| Tag | Długość | Wartość | Znaczenie |
|-----|---------|---------|-----------|
| `04` | `01` | `16` (22) | LED GPIO = GP22 |
| `0C` | `01` | `03` | LED driver = WS2812 |
| `08` | `01` | `0F` (15) | Timeout = 15s |

### Zmiana jasności LED

Jasność 10 (z 15):

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 03 05010A"
```

Payload: `05 01 0A` → PHY_LED_BTNESS = 10

### Ustawienie nazwy produktu

Nazwa "My FIDO Key":

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

### Włączenie opcji (LED dimmable + LED steady)

Flagi: `0x02 | 0x08 = 0x000A`

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 04 06 02 000A"
```

Payload: `06 02 000A` → PHY_OPTS = DIMM + STEADY

### Włączenie krzywej secp256k1

Flagi: domyślne + secp256k1 (`0x08`):

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 06 0A 04 00000008"
```

Payload: `0A 04 00000008` → PHY_ENABLED_CURVES = secp256k1

### Odczyt aktualnej konfiguracji PHY

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801E0100"
```

### Odczyt statusu Secure Boot

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801E0300"
```

### Włączenie Secure Boot (klucz 0, bez blokady)

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801D0000"
```

### Włączenie Secure Boot z blokadą (klucz 0)

```bash
opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801D0001"
```

**Uwaga:** Secure Boot z blokadą jest nieodwracalny. Wymaga WebUSB.
