from __future__ import annotations

import random
from abc import ABC, abstractmethod

from rheocalc32.constants import InstrumentModel, Spindle


class InstrumentError(RuntimeError):
    pass


class InstrumentDriver(ABC):
    """Common interface for anything that can drive a rotational
    viscometer/rheometer: set a target speed/temperature and read back
    the measured torque, speed and temperature."""

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def set_speed(self, rpm: float) -> None: ...

    @abstractmethod
    def set_temperature(self, temp_c: float) -> None: ...

    @abstractmethod
    def read(self) -> tuple[float, float, float]:
        """Returns (rpm, torque_pct, temp_c)."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool: ...


class SimulatedInstrument(InstrumentDriver):
    """Generates plausible torque readings for a chosen fluid model so
    the application can be exercised end-to-end without real hardware.
    """

    def __init__(self, spindle: Spindle, instrument_model: InstrumentModel,
                 fluid_model: str = "power_law",
                 k: float = 2.0, n: float = 0.8, tau0: float = 0.0,
                 mu: float = 50.0, noise_pct: float = 1.5):
        self._spindle = spindle
        self._model = instrument_model
        self.fluid_model = fluid_model
        self.k = k
        self.n = n
        self.tau0 = tau0
        self.mu = mu
        self.noise_pct = noise_pct
        self._connected = False
        self._rpm = 0.0
        self._temp = 25.0

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def set_speed(self, rpm: float) -> None:
        if not self._connected:
            raise InstrumentError("Instrument not connected")
        self._rpm = max(0.0, rpm)

    def set_temperature(self, temp_c: float) -> None:
        if not self._connected:
            raise InstrumentError("Instrument not connected")
        self._temp = temp_c

    def _shear_stress(self, shear_rate: float) -> float:
        if self.fluid_model == "newtonian":
            return self.mu * shear_rate
        if self.fluid_model == "power_law":
            return self.k * shear_rate**self.n
        if self.fluid_model == "bingham":
            return self.tau0 + self.mu * shear_rate
        if self.fluid_model == "herschel_bulkley":
            return self.tau0 + self.k * shear_rate**self.n
        if self.fluid_model == "casson":
            sqrt_tau = (self.tau0**0.5) + (self.mu**0.5) * (shear_rate**0.5)
            return sqrt_tau**2
        raise ValueError(f"Unknown fluid model: {self.fluid_model}")

    def read(self) -> tuple[float, float, float]:
        if not self._connected:
            raise InstrumentError("Instrument not connected")
        # Use an effective SRC of 1.0 when the spindle has no true shear
        # rate (SRC == 0) purely so the simulator can still drive a
        # plausible torque signal; real shear rate/stress reporting
        # still follows the DV3T Appendix D rule (0 when SRC == 0).
        src_for_sim = self._spindle.src or 1.0
        shear_rate = src_for_sim * self._rpm
        torque_pct = 0.0
        if shear_rate > 0 and self._rpm > 0:
            stress = self._shear_stress(shear_rate)
            # torque_pct = stress / (TK * SMC * SRC); rearranged from the
            # DV3T Appendix D relation shear_stress = TK*SMC*SRC*%Torque
            denom = self._model.tk * self._spindle.smc * src_for_sim
            torque_pct = stress / denom if denom else 0.0
            torque_pct *= 1.0 + random.uniform(-self.noise_pct, self.noise_pct) / 100.0
        temp = self._temp + random.uniform(-0.05, 0.05)
        return self._rpm, max(0.0, min(100.0, torque_pct)), temp


# ---------------------------------------------------------------------------
# SerialInstrument: real hardware over USB / RS-232.
#
# IMPORTANT: Brookfield does not publish the exact byte-level command set
# the DV3T/DV3T-family rheometer speaks to RheoCalc/RheocalcT over its
# USB-serial link. The commands below are a best-effort placeholder
# ASCII protocol (plain-text command + CR, comma-separated reply),
# modeled on Brookfield's legacy DV-II+/DV-III "Standard Serial Command"
# style. They are NOT guaranteed to match your DV3 Ultra+ firmware.
#
# To adapt this to your real instrument:
#   1. Capture USB traffic between RheocalcT and the instrument (e.g.
#      with a USB protocol analyzer, or by sniffing the virtual COM
#      port RheocalcT opens), or get the protocol doc from Brookfield
#      support.
#   2. Edit only the four COMMAND TEMPLATE strings below to match.
# Everything else (the public connect/set_speed/set_temperature/read
# interface used by the rest of the app) stays the same.
# ---------------------------------------------------------------------------

# --- COMMAND TEMPLATES (edit to match your instrument) --------------------
CMD_SET_SPEED = "SS{rpm:07.1f}"          # set spindle speed in RPM
CMD_SET_TEMPERATURE = "ST{temp:07.1f}"   # set target temperature in deg C
CMD_READ = "RD"                          # request a measurement reply
# Expected reply to CMD_READ: "<rpm>,<torque_pct>,<temp_c>"
# ---------------------------------------------------------------------------


class SerialInstrument(InstrumentDriver):
    """Driver for a real DV3T-family rheometer over its USB (virtual COM
    port) or RS-232 link. See the protocol caveat above the COMMAND
    TEMPLATE block — verify/adjust the command strings against your
    instrument before relying on this for measurements.
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

    @staticmethod
    def list_ports() -> list[str]:
        """Returns the device names of available serial ports (including
        the USB virtual COM port a DV3T enumerates as when plugged in)."""
        from serial.tools import list_ports

        return [p.device for p in list_ports.comports()]

    def connect(self) -> None:
        import serial  # imported lazily so the simulated driver works without pyserial

        self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def disconnect(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def _command(self, cmd: str) -> str:
        if not self.is_connected:
            raise InstrumentError("Instrument not connected")
        self._serial.write((cmd + "\r").encode("ascii"))
        return self._serial.readline().decode("ascii", errors="replace").strip()

    def set_speed(self, rpm: float) -> None:
        self._command(CMD_SET_SPEED.format(rpm=rpm))

    def set_temperature(self, temp_c: float) -> None:
        self._command(CMD_SET_TEMPERATURE.format(temp=temp_c))

    def read(self) -> tuple[float, float, float]:
        reply = self._command(CMD_READ)
        try:
            rpm_s, torque_s, temp_s = reply.split(",")
            return float(rpm_s), float(torque_s), float(temp_s)
        except ValueError as exc:
            raise InstrumentError(
                f"Unexpected instrument reply: {reply!r}. The command set in "
                "instruments.py (CMD_SET_SPEED/CMD_SET_TEMPERATURE/CMD_READ) "
                "likely needs adjusting for your instrument's firmware."
            ) from exc
