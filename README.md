# SOFAR Inverter G3 + LSW-3/LSE
Niewielkie narzędzie do odczytu danych z falowników SOFAR K-TLX G3 poprzez rejestrator danych Solarman (LSW-3/LSE).

Projekt ten bazuje na pracy użytkowników GitHub: @jlopez77 (kod protokołu rejestratora/MODBUS) i @MichaluxPL (tłumaczenie i modyfikacje kodu). Linki do ich repozytoriów:

*Thanks to @jlopez77 https://github.com/jlopez77 for logger/MODBUS protocol code.*
*Thanks to @MichaluxPL https://github.com/MichaluxPL
*Thanks to @pawsuch https://github.com/pawsuch/Sofar_G3_LSW3

# Wymagane moduły Pythona
Aby uruchomić skrypt, wymagane są następujące moduły Pythona:
```
libscrc
```

# Konfiguracja

Edytuj plik config.cfg i wprowadź następujące dane:
```
[SofarInverter]
inverter_ip=X.X.X.X             # IP rejestratora danych
inverter_port=8899              # port rejestratora danych
inverter_sn=XXXXXXXXXX          # S/N rejestratora danych
verbose=0                       # Ustaw na 1, aby zaprezentować dodatkowe informacje (rejestry, pakiety binarne itp.)
```

# Podziękowania
Kod powstał przy wsparciu modelu językowego GPT4
