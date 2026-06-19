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

from rheocalc32.instruments import SerialInstrument


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
            "Note: the exact command protocol for the DV3T family is not\n"
            "publicly documented by Brookfield. This connects over the port\n"
            "above using a best-effort command set (see instruments.py) -\n"
            "verify readings against the instrument's own display and adjust\n"
            "the CMD_* templates there if needed."
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
