# pico-fido Test Suite

Functional tests for the pico-fido authenticator. Tests communicate with a real device over USB HID (CTAP) and PC/SC (CCID/OATH).

## Requirements

```bash
pip install fido2 pyscard python-inputimeout pytest
```

A pico-fido device must be connected via USB.

## Running Tests

```bash
# All tests
pytest tests/

# Single file
pytest tests/pico-fido/test_020_register.py

# Single test
pytest tests/pico-fido/test_020_register.py::test_algorithms
```

## Safety Warning

Tests perform **destructive operations** on the connected device:

| Risk | Operation | Impact |
|------|-----------|--------|
| **HIGH** | FIDO2 factory reset (`authenticatorReset`) | Wipes all FIDO2 credentials and PIN |
| **MEDIUM** | OATH reset (INS 0x04, P1=0xDE P2=0xAD) | Wipes all OATH credentials |
| **LOW** | Manual reboot prompt | Waits for user to press Enter |

**No tests** trigger secure boot, PHY configuration changes, or BOOTSEL mode.

Use a **dedicated test device** — do not run on a device with production credentials.

## Test Files

| File | Feature | Description |
|------|---------|-------------|
| `test_000_getinfo.py` | CTAP2 GetInfo | Device info, versions, options, PIN protocols |
| `test_010_pin.py` | ClientPIN | PIN lockout after wrong attempts, retry counter |
| `test_020_register.py` | MakeCredential | Credential registration, parameter validation, supported algorithms (ES256, ES384, ES512, ES256K, EdDSA) |
| `test_021_authenticate.py` | GetAssertion | Authentication, signature verification, allowList filtering, silent auth |
| `test_022_discoverable.py` | Resident Keys | Discoverable credential storage, user info, overwrite, max capacity |
| `test_031_blob.py` | credBlob + largeBlob | Blob storage at creation, retrieval, large blob read/write |
| `test_033_credprotect.py` | credProtect | Credential protection policies (Optional, OptionalWithList, Required) |
| `test_035_hmac_secret.py` | hmac-secret | HMAC-based secret derivation, salt validation, determinism |
| `test_037_minpinlength.py` | minPinLength | Minimum PIN length enforcement, authenticator config |
| `test_040_cred_mgmt.py` | Credential Management | Enumerate RPs/credentials, delete, metadata |
| `test_051_ctap1_interop.py` | CTAP1/CTAP2 Interop | Cross-protocol credential usage (U2F ↔ FIDO2) |
| `test_052_u2f.py` | U2F / CTAP1 | U2F register/authenticate, version, error codes, counter monotonicity |
| `test_055_hid.py` | CTAPHID Transport | HID framing, ping, channel management, busy/timeout/abort handling |
| `test_070_oath.py` | OATH (TOTP/HOTP) | OATH credential lifecycle via CCID: put, list, calculate, delete, auth |

## Test Infrastructure

### Key Files

- `conftest.py` — `Device` class wrapping `fido2` library, shared fixtures (`device`, `resetdevice`, `select_oath`, etc.)
- `utils.py` — helpers: `send_apdu()`, `verify()`, `generate_random_user()`, `ES256K` algorithm support

### Fixtures

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `device` | session | Shared Device instance (USB HID) |
| `info` | module | CTAP2 authenticator info |
| `MCRes` / `GARes` | module | MakeCredential / GetAssertion result pair |
| `MCRes_DC` / `GARes_DC` | module | Discoverable credential result pair |
| `RegRes` / `AuthRes` | module | CTAP1/U2F registration / authentication |
| `resetdevice` | module | Device after factory reset |
| `client_pin` | class | ClientPin object (PIN set to `12345678`) |
| `ccid_card` | class | PC/SC card connection |
| `select_oath` | class | OATH applet selected |
| `reset_oath` | class | OATH applet reset |

### Default PIN

All tests that require a PIN use: `12345678`
