from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from viscobridge.instruments import SerialInstrument


class ConnectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Instrument")
        layout = QVBoxLayout(self)

        self.serial_radio = QRadioButton("Real instrument (USB / RS-232)")
        self.sim_radio = QRadioButton("Simulated instrument (no hardware)")
        self.serial_radio.setChecked(True)
        layout.addWidget(self.serial_radio)

        form = QFormLayout()
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        refresh_btn = QPushButton("Refresh ports")
        refresh_btn.clicked.connect(self._refresh_ports)
        self.baud_spin = QSpinBox()
        self.baud_spin.setRange(300, 921600)
        self.baud_spin.setValue(9600)
        form.addRow("Port", self.port_combo)
        form.addRow("", refresh_btn)
        form.addRow("Baud rate", self.baud_spin)
        layout.addLayout(form)

        layout.addWidget(QLabel(
            "Uses Brookfield's documented DV-III Ultra / DV3 Ultra+ command\n"
            "set (Appendix G): 9600 baud, 8-N-1, no handshake. If you're on a\n"
            "different model's USB virtual COM port, verify readings against\n"
            "the instrument's own display first."
        ))
        layout.addWidget(self.sim_radio)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh_ports()

    def _refresh_ports(self):
        self.port_combo.clear()
        try:
            ports = SerialInstrument.list_ports()
        except Exception:
            ports = []
        self.port_combo.addItems(ports)

    def use_simulated(self) -> bool:
        return self.sim_radio.isChecked()

    def port(self) -> str:
        return self.port_combo.currentText()

    def baudrate(self) -> int:
        return self.baud_spin.value()
