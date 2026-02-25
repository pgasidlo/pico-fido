# Tenstar RP2350-USB — konfiguracja Pico FIDO

Instrukcja konfiguracji płytki Tenstar RP2350-USB z firmware pico-fido jako klucza FIDO2/SSH.

## Specyfikacja płytki

| Parametr | Wartość |
|----------|---------|
| Chip | RP2350A (dual-core) |
| Flash | 16 MB |
| USB | USB-A male |
| LED | WS2812 RGB na GP22 |
| Przycisk | BOOTSEL (QSPI CS) |
| PICO_BOARD | `pico2` |

## Wymagania

- `opensc-tool` (pakiet `opensc`)
- `pcscd` (pakiet `pcsc-lite`)
- OpenSSH 8.2+ (obsługa kluczy FIDO2)
- Firmware pico-fido wgrane na płytkę

## 1. Konfiguracja CCID (Info.plist)

Sterownik CCID musi znać VID/PID urządzenia. Dodaj identyfikatory Raspberry Pi do pliku konfiguracyjnego:

**Plik:** `/usr/lib/pcsc/drivers/ifd-ccid.bundle/Contents/Info.plist`

Dodaj wpisy na pierwszej pozycji w trzech tablicach (`ifdVendorID`, `ifdProductID`, `ifdFriendlyName`):

```xml
<key>ifdVendorID</key>
<array>
    <string>0x2E8A</string>
    <!-- reszta wpisów... -->

<key>ifdProductID</key>
<array>
    <string>0x10FE</string>
    <!-- reszta wpisów... -->

<key>ifdFriendlyName</key>
<array>
    <string>Pico Key</string>
    <!-- reszta wpisów... -->
```

Po edycji zrestartuj serwis:

```bash
sudo systemctl restart pcscd
```

Weryfikacja — urządzenie powinno być widoczne:

```
$ opensc-tool -l
# Detected readers (pcsc)
Nr.  Card  Features  Name
0    Yes             Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00
1    No              Broadcom Corp 58200 [Contacted SmartCard] (0123456789ABCD) 01 00
2    No              Broadcom Corp 58200 [Contactless SmartCard] (0123456789ABCD) 02 00
```

## 2. Konfiguracja PHY (LED + przycisk)

SELECT rescue appletu i zapis PHY można wykonać jedną komendą:

```
$ opensc-tool -s "00A40400 08 A0583FC19B7E4F21" -s "801C0100 09 0401160C010308010F"
Using reader with a card: Pico Key [Pico Key CCID OTP FIDO Interfac] (8D94997D9577EE53) 00 00
Sending: 00 A4 04 00 08 A0 58 3F C1 9B 7E 4F 21
Received (SW1=0x90, SW2=0x00):
01 02 07 04 8D 94 99 7D 95 77 EE 53 .......}.w.S
Sending: 80 1C 01 00 09 04 01 16 0C 01 03 08 01 0F
Received (SW1=0x90, SW2=0x00)
```

AID rescue appletu: `A0 58 3F C1 9B 7E 4F 21`

### Struktura komendy APDU

| Bajt | Wartość | Opis |
|------|---------|------|
| CLA | `0x80` | Klasa proprietary (nie `0x00` — zwróci `6E00`) |
| INS | `0x1C` | WRITE |
| P1 | `0x01` | PHY data |
| P2 | `0x00` | — |
| Lc | `0x09` | Długość payload (9 bajtów) |

### Struktura payload (TLV)

| Tag | Długość | Wartość | Opis |
|-----|---------|---------|------|
| `0x04` | `0x01` | `0x16` (22) | LED GPIO — GP22 |
| `0x0C` | `0x01` | `0x03` | LED driver — WS2812 |
| `0x08` | `0x01` | `0x0F` (15) | Timeout przycisku — 15 sekund |

## 3. Weryfikacja

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

Po poprawnej konfiguracji:
- LED WS2812 świeci podczas operacji kryptograficznych
- BOOTSEL wymaga 15-sekundowego przytrzymania do autoryzacji

## 4. Konfiguracja SSH z kluczem FIDO2

### Generowanie klucza resident Ed25519-SK

```bash
ssh-keygen -t ed25519-sk -O resident -O verify-required -C "pico-fido"
```

Klucz resident jest przechowywany na urządzeniu — można go pobrać na dowolnym komputerze.

### Alternatywnie — ECDSA-SK

```bash
ssh-keygen -t ecdsa-sk -C "pico-fido"
```

### Kopiowanie klucza na serwer

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_sk.pub user@server
```

### Użycie

```bash
ssh -i ~/.ssh/id_ed25519_sk user@server
```

Podczas logowania urządzenie poprosi o potwierdzenie przyciskiem (BOOTSEL).

## Rozwiązywanie problemów

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| `SW1=0x6E` | Zły bajt CLA (`0x00`) | Użyj CLA `0x80` |
| LED nie świeci | Domyślny GPIO 25 zamiast 22 | Skonfiguruj PHY_LED_GPIO=22 |
| Przycisk nie reaguje | Timeout=0 (domyślny) | Ustaw PHY_UP_BTN na 15 |
| Urządzenie niewidoczne | Brak VID/PID w Info.plist | Dodaj `2E8A:10FE` i restart pcscd |
