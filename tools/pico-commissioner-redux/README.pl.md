# pico-commissioner-redux

Narzędzie konfiguracji PHY dla urządzeń pico-fido.

Komunikuje się z apletem rescue przez PC/SC w celu odczytu i zapisu konfiguracji sprzętowej (LED, USB, przyciski, krzywe, secure boot).

## Instalacja

```bash
pip install pyscard
```

## Użycie

### Odczyt aktualnej konfiguracji

```bash
python pico_commissioner.py read
```

### Zapis konfiguracji (CLI)

```bash
# Ustawienie LED i przycisku
python pico_commissioner.py write --led-gpio 22 --led-driver ws2812 --button-timeout 15

# Ustawienie VID:PID i nazwy produktu
python pico_commissioner.py write --vid-pid 2E8A:10FE --product-name "Pico Key"

# Jasność i opcje
python pico_commissioner.py write --led-brightness 10 --opts wcid dimmable

# Wybrane krzywe i interfejsy
python pico_commissioner.py write --curves secp256r1 ed25519 --usb-interfaces ccid hid
```

### Zapis konfiguracji (tryb interaktywny)

```bash
python pico_commissioner.py write
# Bez argumentów → interaktywne menu pyta o każdą opcję
# Enter = pomiń (zachowaj aktualną wartość)
```

### Secure boot

```bash
# Status
python pico_commissioner.py secure-boot status

# Włączenie (slot klucza 0)
python pico_commissioner.py secure-boot enable --key 0

# Włączenie z blokadą OTP (NIEODWRACALNE!)
python pico_commissioner.py secure-boot enable --key 0 --lock
```

### Restart

```bash
# Normalny restart
python pico_commissioner.py reboot

# Restart do BOOTSEL (aktualizacja firmware)
python pico_commissioner.py reboot --bootsel
```

## Referencja opcji

| Opcja | Wartości |
|---|---|
| `--led-driver` | `pico`, `pimoroni`, `ws2812`, `cyw43`, `neopixel`, `none` |
| `--opts` | `wcid`, `dimmable`, `no-power-reset`, `led-steady` |
| `--curves` | `secp256r1`, `secp384r1`, `secp521r1`, `secp256k1`, `bp256r1`, `bp384r1`, `bp512r1`, `ed25519`, `ed448`, `curve25519`, `curve448` |
| `--usb-interfaces` | `ccid`, `wcid`, `hid`, `kb` |
| `--led-brightness` | `0`–`15` |
