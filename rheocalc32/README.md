# RheoCalc32 (Python / PySide6)

A modern reimplementation of Brookfield's RheoCalc32 rotational
viscometer/rheometer control and analysis software.

## Features

- **Method editor** — sample info, spindle selection (with editable
  SRC/SMC calibration constants), and a step table (speed ramps, speed
  holds, time holds, temperature ramps).
- **Instrument drivers** — pluggable `InstrumentDriver` interface with a
  `SimulatedInstrument` (generates realistic torque from a chosen fluid
  model: Newtonian, Power Law, Bingham, Herschel-Bulkley, Casson) for
  testing without hardware, and a `SerialInstrument` for real
  RS-232/USB-serial Brookfield-protocol instruments.
- **Live acquisition & plotting** — real-time viscosity vs. shear rate,
  torque vs. time, and temperature vs. time plots while a run executes.
- **Flow curve model fitting** — least-squares fits to Newtonian, Power
  Law, Bingham, Herschel-Bulkley, and Casson models with R² and fitted
  parameters (consistency index, flow index, yield stress, viscosity).
- **Run management** — save/load runs as `.rc32` (JSON) files, export
  to CSV.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python -m rheocalc32
```

## Notes on accuracy and connecting to a real DV3T / DV3 Ultra+

The spindle SMC/SRC values and instrument-model TK (torque) constants
bundled in `constants.py` are taken directly from Brookfield's published
DV3T Operating Instructions (Manual No. M13-167-A0415), Appendix D —
`Viscosity (cP) = TK * SMC * 100 * %Torque / RPM`,
`Shear Rate (1/s) = SRC * RPM`,
`Shear Stress (dyne/cm^2) = TK * SMC * SRC * %Torque`.
If you're using a Special Spindle (custom geometry), edit SMC/SRC in the
Method panel to match its calibration certificate.

**Real hardware caveat:** Brookfield does not publish the byte-level
command protocol the DV3T speaks over its USB virtual-COM-port link to
RheoCalc/RheocalcT — only Brookfield's own software is documented to
use it. `instruments.py` ships a best-effort placeholder ASCII command
set (`CMD_SET_SPEED`, `CMD_SET_TEMPERATURE`, `CMD_READ`) modeled on
Brookfield's older DV-II+/DV-III serial style, clearly marked at the top
of the file. If it doesn't talk to your unit out of the box:

1. Capture the USB traffic between RheocalcT and the instrument (USB
   protocol analyzer, or by sniffing the virtual COM port RheocalcT
   opens), or request the protocol document from Brookfield support.
2. Edit just the `CMD_*` template strings in `instruments.py` to match —
   the rest of the driver interface (`connect`/`set_speed`/
   `set_temperature`/`read`) doesn't need to change.

Use **Connect...** in the toolbar to pick "Real instrument" and a serial
port (auto-detected, including USB-serial enumeration), or "Simulated
instrument" to exercise the app without hardware.
