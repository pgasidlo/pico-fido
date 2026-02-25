# pico-commissioner-redux

PHY configuration tool for pico-fido devices.

Communicates with the rescue applet over PC/SC to read and write hardware configuration (LED, USB, buttons, curves, secure boot).

## Installation

```bash
pip install pyscard
```

## Usage

### Read current configuration

```bash
python pico_commissioner.py read
```

### Write configuration (CLI)

```bash
# Set LED and button
python pico_commissioner.py write --led-gpio 22 --led-driver ws2812 --button-timeout 15

# Set VID:PID and product name
python pico_commissioner.py write --vid-pid 2E8A:10FE --product-name "Pico Key"

# Set brightness and options
python pico_commissioner.py write --led-brightness 10 --opts wcid dimmable

# Enable specific curves and interfaces
python pico_commissioner.py write --curves secp256r1 ed25519 --usb-interfaces ccid hid

# Combine multiple settings
python pico_commissioner.py write \
  --vid-pid 2E8A:10FE \
  --led-gpio 22 \
  --led-driver ws2812 \
  --led-brightness 10 \
  --button-timeout 15 \
  --product-name "Pico Key" \
  --opts wcid dimmable \
  --curves secp256r1 secp384r1 ed25519 \
  --usb-interfaces ccid hid
```

### Write configuration (interactive)

```bash
python pico_commissioner.py write
# No arguments → interactive menu prompts for each option
# Press Enter to skip any field (keeps current value)
```

### Secure boot

```bash
# Check status
python pico_commissioner.py secure-boot status

# Enable (key slot 0)
python pico_commissioner.py secure-boot enable --key 0

# Enable and lock OTP (IRREVERSIBLE!)
python pico_commissioner.py secure-boot enable --key 0 --lock
```

### Reboot

```bash
# Normal reboot
python pico_commissioner.py reboot

# Reboot into BOOTSEL (firmware update)
python pico_commissioner.py reboot --bootsel
```

## Options reference

| Option | Values |
|---|---|
| `--led-driver` | `pico`, `pimoroni`, `ws2812`, `cyw43`, `neopixel`, `none` |
| `--opts` | `wcid`, `dimmable`, `no-power-reset`, `led-steady` |
| `--curves` | `secp256r1`, `secp384r1`, `secp521r1`, `secp256k1`, `bp256r1`, `bp384r1`, `bp512r1`, `ed25519`, `ed448`, `curve25519`, `curve448` |
| `--usb-interfaces` | `ccid`, `wcid`, `hid`, `kb` |
| `--led-brightness` | `0`–`15` |
