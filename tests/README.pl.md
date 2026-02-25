# Testy pico-fido

Testy funkcjonalne authenticatora pico-fido. Komunikacja z urządzeniem odbywa się przez USB HID (CTAP) oraz PC/SC (CCID/OATH).

## Wymagania

```bash
pip install fido2 pyscard python-inputimeout pytest
```

Urządzenie pico-fido musi być podłączone przez USB.

## Uruchamianie testów

```bash
# Wszystkie testy
pytest tests/

# Pojedynczy plik
pytest tests/pico-fido/test_020_register.py

# Pojedynczy test
pytest tests/pico-fido/test_020_register.py::test_algorithms
```

## Ostrzeżenie bezpieczeństwa

Testy wykonują **destrukcyjne operacje** na podłączonym urządzeniu:

| Ryzyko | Operacja | Skutek |
|--------|----------|--------|
| **WYSOKIE** | Factory reset FIDO2 (`authenticatorReset`) | Kasuje wszystkie klucze FIDO2 i PIN |
| **ŚREDNIE** | Reset OATH (INS 0x04, P1=0xDE P2=0xAD) | Kasuje wszystkie klucze OATH |
| **NISKIE** | Ręczny restart | Czeka na wciśnięcie Enter |

Żaden test **nie** uruchamia secure boot, nie zmienia konfiguracji PHY ani nie wchodzi w tryb BOOTSEL.

Używaj **dedykowanego urządzenia testowego** — nie uruchamiaj na urządzeniu z produkcyjnymi kluczami.

## Pliki testowe

| Plik | Funkcjonalność | Opis |
|------|----------------|------|
| `test_000_getinfo.py` | CTAP2 GetInfo | Informacje o urządzeniu, wersje, opcje, protokoły PIN |
| `test_010_pin.py` | ClientPIN | Blokada PIN po błędnych próbach, licznik prób |
| `test_020_register.py` | MakeCredential | Rejestracja kluczy, walidacja parametrów, wspierane algorytmy (ES256, ES384, ES512, ES256K, EdDSA) |
| `test_021_authenticate.py` | GetAssertion | Uwierzytelnianie, weryfikacja podpisów, filtrowanie allowList, tryb cichy |
| `test_022_discoverable.py` | Resident Keys | Klucze discoverable, dane użytkownika, nadpisywanie, limit pojemności |
| `test_031_blob.py` | credBlob + largeBlob | Przechowywanie blobów, odczyt, zapis dużych blobów |
| `test_033_credprotect.py` | credProtect | Polityki ochrony kluczy (Optional, OptionalWithList, Required) |
| `test_035_hmac_secret.py` | hmac-secret | Wyprowadzanie sekretów HMAC, walidacja soli, determinizm |
| `test_037_minpinlength.py` | minPinLength | Wymuszanie minimalnej długości PIN, konfiguracja authenticatora |
| `test_040_cred_mgmt.py` | Credential Management | Enumeracja RP/kluczy, usuwanie, metadane |
| `test_051_ctap1_interop.py` | Interop CTAP1/CTAP2 | Używanie kluczy między protokołami (U2F ↔ FIDO2) |
| `test_052_u2f.py` | U2F / CTAP1 | Rejestracja/uwierzytelnianie U2F, wersja, kody błędów, monotoniczność licznika |
| `test_055_hid.py` | Transport CTAPHID | Ramkowanie HID, ping, zarządzanie kanałami, obsługa busy/timeout/abort |
| `test_070_oath.py` | OATH (TOTP/HOTP) | Cykl życia kluczy OATH przez CCID: dodawanie, lista, obliczanie, usuwanie, autoryzacja |

## Infrastruktura testowa

### Kluczowe pliki

- `conftest.py` — klasa `Device` opakowująca bibliotekę `fido2`, współdzielone fixture'y (`device`, `resetdevice`, `select_oath`, itp.)
- `utils.py` — helpery: `send_apdu()`, `verify()`, `generate_random_user()`, obsługa algorytmu `ES256K`

### Fixture'y

| Fixture | Zakres | Przeznaczenie |
|---------|--------|---------------|
| `device` | sesja | Współdzielona instancja Device (USB HID) |
| `info` | moduł | Informacje CTAP2 authenticatora |
| `MCRes` / `GARes` | moduł | Para wyników MakeCredential / GetAssertion |
| `MCRes_DC` / `GARes_DC` | moduł | Para wyników dla kluczy discoverable |
| `RegRes` / `AuthRes` | moduł | Rejestracja / uwierzytelnianie CTAP1/U2F |
| `resetdevice` | moduł | Urządzenie po factory reset |
| `client_pin` | klasa | Obiekt ClientPin (PIN ustawiony na `12345678`) |
| `ccid_card` | klasa | Połączenie PC/SC |
| `select_oath` | klasa | Wybrany aplet OATH |
| `reset_oath` | klasa | Zresetowany aplet OATH |

### Domyślny PIN

Wszystkie testy wymagające PIN używają: `12345678`
