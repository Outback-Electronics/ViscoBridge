from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from viscobridge.constants import DEFAULT_SPINDLES, INSTRUMENT_MODELS, STEP_TYPES
from viscobridge.models import Sample, TestMethod, TestStep

STEP_COLUMNS = ["Step Type", "Start RPM", "End RPM", "Duration (s)", "Interval (s)", "Target Temp (C)"]


class MethodEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.method = TestMethod(steps=[TestStep()])
        self.sample = Sample()

        layout = QVBoxLayout(self)

        sample_box = QGroupBox("Sample")
        form = QFormLayout(sample_box)
        self.name_edit = QLineEdit(self.sample.name)
        self.operator_edit = QLineEdit(self.sample.operator)
        self.notes_edit = QLineEdit(self.sample.notes)
        form.addRow("Sample name", self.name_edit)
        form.addRow("Operator", self.operator_edit)
        form.addRow("Notes", self.notes_edit)
        layout.addWidget(sample_box)

        method_box = QGroupBox("Method / Instrument / Spindle")
        mform = QFormLayout(method_box)
        self.method_name_edit = QLineEdit(self.method.name)

        self.model_combo = QComboBox()
        for model in INSTRUMENT_MODELS:
            self.model_combo.addItem(f"{model.name} (TK={model.tk})", model)
        self.model_combo.setCurrentIndex(5)  # DV3TRV

        self.spindle_combo = QComboBox()
        for sp in DEFAULT_SPINDLES:
            self.spindle_combo.addItem(f"{sp.name} ({sp.entry_code})", sp)
        self.spindle_combo.currentIndexChanged.connect(self._on_spindle_changed)

        self.src_spin = QDoubleSpinBox()
        self.src_spin.setDecimals(5)
        self.src_spin.setRange(0.0, 100000.0)
        self.smc_spin = QDoubleSpinBox()
        self.smc_spin.setDecimals(5)
        self.smc_spin.setRange(0.0, 1000000.0)
        self._on_spindle_changed(0)

        mform.addRow("Method name", self.method_name_edit)
        mform.addRow("Instrument model", self.model_combo)
        mform.addRow("Spindle", self.spindle_combo)
        mform.addRow("SRC (1/s per RPM)", self.src_spin)
        mform.addRow("SMC (Spindle Multiplier Constant)", self.smc_spin)
        layout.addWidget(method_box)

        steps_box = QGroupBox("Test Steps")
        steps_layout = QVBoxLayout(steps_box)
        self.steps_table = QTableWidget(0, len(STEP_COLUMNS))
        self.steps_table.setHorizontalHeaderLabels(STEP_COLUMNS)
        self.steps_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        steps_layout.addWidget(self.steps_table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Step")
        remove_btn = QPushButton("Remove Step")
        add_btn.clicked.connect(self.add_step)
        remove_btn.clicked.connect(self.remove_step)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        steps_layout.addLayout(btn_row)
        layout.addWidget(steps_box)

        self.add_step()

    def _on_spindle_changed(self, index: int):
        sp = self.spindle_combo.currentData()
        if sp is not None:
            self.src_spin.setValue(sp.src)
            self.smc_spin.setValue(sp.smc)

    def add_step(self):
        row = self.steps_table.rowCount()
        self.steps_table.insertRow(row)
        type_combo = QComboBox()
        type_combo.addItems(STEP_TYPES)
        self.steps_table.setCellWidget(row, 0, type_combo)
        defaults = [1.0, 100.0, 60.0, 1.0, 25.0]
        for col, val in enumerate(defaults, start=1):
            self.steps_table.setItem(row, col, QTableWidgetItem(str(val)))

    def remove_step(self):
        row = self.steps_table.currentRow()
        if row >= 0:
            self.steps_table.removeRow(row)

    def get_method(self) -> TestMethod:
        sp = self.spindle_combo.currentData()
        spindle = type(sp)(name=sp.name, entry_code=sp.entry_code, smc=self.smc_spin.value(),
                            src=self.src_spin.value(), description=sp.description)
        model = self.model_combo.currentData()
        steps = []
        for row in range(self.steps_table.rowCount()):
            type_combo = self.steps_table.cellWidget(row, 0)
            step_type = type_combo.currentText() if type_combo else STEP_TYPES[0]
            values = [float(self.steps_table.item(row, c).text()) for c in range(1, 6)]
            steps.append(TestStep(step_type, *values))
        return TestMethod(
            name=self.method_name_edit.text(),
            instrument_model=model,
            spindle=spindle,
            container=self.method.container,
            steps=steps,
        )

    def get_sample(self) -> Sample:
        return Sample(
            name=self.name_edit.text(),
            operator=self.operator_edit.text(),
            notes=self.notes_edit.text(),
        )
