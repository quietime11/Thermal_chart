import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QFileDialog, QMessageBox, QLineEdit, QRadioButton,
                             QButtonGroup, QListWidget, QTextEdit, QSlider,
                             QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
                             QSplitter, QScrollArea, QCheckBox, QComboBox,
                             QSpinBox, QProgressBar, QStatusBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

class ThermalAnalyzerPyQt(QMainWindow):
    # Signal to notify when setpoint positions change
    setpoint_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.df = None
        self.groups = {}
        self.manual_groups = {}
        self.fig = None
        self.canvas = None
        self.analysis_dialog = None  # Keep reference to analysis dialog
        self.setpoint_sliders = []
        
        # Prevent recursion in auto-update
        self._updating = False
        
        self.init_ui()
        self.setWindowTitle("🌡️ HVAC Thermal Test Analyzer - PyQt5 Edition")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Set application style
        self.set_style()
        
        # Show status message
        self.status_bar.showMessage("Ready - Upload CSV file to start analysis")

    def set_style(self):
        """Set modern light theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
                color: #333333;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
                color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333333;
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QLineEdit, QTextEdit {
                background-color: #ffffff;
                border: 2px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                color: #333333;
            }
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #cccccc;
                border-radius: 4px;
                color: #333333;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QRadioButton {
                color: #333333;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 13px;
                height: 13px;
            }
            QLabel {
                color: #333333;
            }
            QSlider::groove:horizontal {
                border: 1px solid #cccccc;
                height: 8px;
                background: #f0f0f0;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #0078d4;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8f8f8;
                gridline-color: #cccccc;
                color: #333333;
            }
            QHeaderView::section {
                background-color: #0078d4;
                color: white;
                padding: 4px;
                border: 1px solid #cccccc;
            }
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                color: #333333;
            }
        """)


    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.setup_tab = QWidget()
        self.chart_tab = QWidget()
        
        self.tab_widget.addTab(self.setup_tab, "🔧 Setup & Configuration")
        self.tab_widget.addTab(self.chart_tab, "📊 Chart & Analysis")
        
        # Setup tab layout
        setup_layout = QHBoxLayout(self.setup_tab)
        
        # Controls panel takes full width of setup tab
        left_panel = self.create_controls_panel()
        setup_layout.addWidget(left_panel)
        
        # Chart tab layout
        chart_layout = QVBoxLayout(self.chart_tab)
        
        # Chart panel (full screen)
        chart_panel = self.create_chart_panel()
        chart_layout.addWidget(chart_panel)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Menu bar
        self.create_menu_bar()

    def signal_list_key_press(self, event):
        """Handle key press events in signal list"""
        # Call the original keyPressEvent first
        QListWidget.keyPressEvent(self.signal_list, event)
        
        # Check if Enter or Return was pressed
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Switch to chart tab if signals are selected
            if self.get_selected_signals():
                self.tab_widget.setCurrentIndex(1)  # Switch to chart tab
                self.status_bar.showMessage("Switched to Chart tab - Chart updated with selected signals", 3000)
            else:
                self.status_bar.showMessage("Please select at least one signal first", 3000)

    def sensor_list_key_press(self, event):
        """Handle key press events in sensor list"""
        # Call the original keyPressEvent first
        QListWidget.keyPressEvent(self.sensor_list, event)
        
        # Check if Enter or Return was pressed
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Try to add manual group if sensors are selected
            if self.sensor_list.selectedItems():
                self.add_manual_group()
            else:
                self.status_bar.showMessage("Please select sensors to group first", 3000)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = file_menu.addAction('Open CSV...')
        open_action.triggered.connect(self.upload_file)
        
        sample_action = file_menu.addAction('Load Sample Data')
        sample_action.triggered.connect(self.load_sample_data)
        
        file_menu.addSeparator()
        
        export_action = file_menu.addAction('Export Data...')
        export_action.triggered.connect(self.export_data)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        summary_action = view_menu.addAction('Show Summary')
        summary_action.triggered.connect(self.show_summary)
        
        setpoint_action = view_menu.addAction('Set Point Analysis')
        setpoint_action.triggered.connect(self.show_setpoint_analysis)

    def create_controls_panel(self):
        # Scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Remove fixed width to allow full width usage
        
        widget = QWidget()
        # Use grid layout for better space utilization
        layout = QGridLayout(widget)
        layout.setSpacing(10)
        
        # File section - spans full width (row 0, cols 0-1)
        file_group = QGroupBox("📂 Data Import")
        file_layout = QVBoxLayout(file_group)
        
        file_button_layout = QHBoxLayout()
        self.upload_btn = QPushButton("📁 Select CSV File")
        self.upload_btn.clicked.connect(self.upload_file)
        self.sample_btn = QPushButton("📋 Load Sample")
        self.sample_btn.clicked.connect(self.load_sample_data)
        
        file_button_layout.addWidget(self.upload_btn)
        file_button_layout.addWidget(self.sample_btn)
        file_layout.addLayout(file_button_layout)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #cccccc; font-style: italic;")
        file_layout.addWidget(self.file_label)
        
        layout.addWidget(file_group, 0, 0, 1, 2)  # Spans 2 columns
        
        # Sensor Grouping Section - Left column
        grouping_group = QGroupBox("🔧 Sensor Grouping Configuration")
        grouping_layout = QVBoxLayout(grouping_group)
        
        # Remove Auto mode, default to Manual only
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode: Manual (Default)"))
        mode_layout.addStretch()
        grouping_layout.addLayout(mode_layout)
        
        # Manual grouping controls
        self.manual_group_widget = QWidget()
        manual_layout = QVBoxLayout(self.manual_group_widget)
        
        # Group name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Group Name:"))
        self.group_name_input = QLineEdit()
        name_layout.addWidget(self.group_name_input)
        manual_layout.addLayout(name_layout)
        
        # Sensor list (will show only unassigned sensors)
        manual_layout.addWidget(QLabel("Available Sensors:"))
        self.sensor_list = QListWidget()
        self.sensor_list.setSelectionMode(QListWidget.MultiSelection)
        self.sensor_list.setMaximumHeight(120)
        # Add Enter key support for sensor list too
        self.sensor_list.keyPressEvent = self.sensor_list_key_press
        manual_layout.addWidget(self.sensor_list)
        
        # Group management buttons
        group_btn_layout = QHBoxLayout()
        self.add_group_btn = QPushButton("➕ Add Group")
        self.remove_group_btn = QPushButton("➖ Remove")
        self.add_group_btn.clicked.connect(self.add_manual_group)
        self.remove_group_btn.clicked.connect(self.remove_manual_group)
        group_btn_layout.addWidget(self.add_group_btn)
        group_btn_layout.addWidget(self.remove_group_btn)
        manual_layout.addLayout(group_btn_layout)
        
        # Current groups display
        manual_layout.addWidget(QLabel("Current Groups:"))
        self.groups_display = QTextEdit()
        self.groups_display.setMaximumHeight(80)
        self.groups_display.setReadOnly(True)
        manual_layout.addWidget(self.groups_display)
        
        # Show manual controls by default
        self.manual_group_widget.setVisible(True)
        grouping_layout.addWidget(self.manual_group_widget)
        
        layout.addWidget(grouping_group, 1, 0)  # Row 1, Column 0

        # Chart settings - Right column  
        chart_group = QGroupBox("📊 Chart Configuration")
        chart_layout = QGridLayout(chart_group)
        
        chart_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_input = QLineEdit("Thermal Analysis Chart")
        # Auto-update when title changes
        self.title_input.textChanged.connect(self.auto_update_chart)
        chart_layout.addWidget(self.title_input, 0, 1)
        
        chart_layout.addWidget(QLabel("Time Unit:"), 1, 0)
        time_layout = QHBoxLayout()
        self.time_group = QButtonGroup()
        self.time_minute = QRadioButton("Minutes")
        self.time_second = QRadioButton("Seconds")
        self.time_minute.setChecked(True)
        self.time_group.addButton(self.time_minute, 0)
        self.time_group.addButton(self.time_second, 1)
        # Auto-update when time unit changes
        self.time_minute.toggled.connect(self.auto_update_chart)
        self.time_second.toggled.connect(self.auto_update_chart)
        time_layout.addWidget(self.time_minute)
        time_layout.addWidget(self.time_second)
        chart_layout.addLayout(time_layout, 1, 1)
        
        chart_layout.addWidget(QLabel("Y-axis:"), 2, 0)
        y_axis_layout = QHBoxLayout()
        self.y_axis_group = QButtonGroup()
        self.y_auto = QRadioButton("Auto")
        self.y_from_zero = QRadioButton("From 0")
        self.y_auto.setChecked(True)
        self.y_axis_group.addButton(self.y_auto, 0)
        self.y_axis_group.addButton(self.y_from_zero, 1)
        # Auto-update when Y-axis changes
        self.y_auto.toggled.connect(self.auto_update_chart)
        self.y_from_zero.toggled.connect(self.auto_update_chart)
        y_axis_layout.addWidget(self.y_auto)
        y_axis_layout.addWidget(self.y_from_zero)
        chart_layout.addLayout(y_axis_layout, 2, 1)
        
        layout.addWidget(chart_group, 1, 1)  # Row 1, Column 1
        
        # Signal selection - spans both columns on row 2
        signal_group = QGroupBox("📊 Signal Selection")
        signal_layout = QVBoxLayout(signal_group)
        
        signal_layout.addWidget(QLabel("Signals to display:"))
        self.signal_list = QListWidget()
        self.signal_list.setSelectionMode(QListWidget.MultiSelection)
        self.signal_list.setMaximumHeight(150)
        # Auto-update when signal selection changes - ONLY trigger chart generation
        self.signal_list.itemSelectionChanged.connect(self.on_signal_selection_changed)
        # Add Enter key support for manual chart update
        self.signal_list.keyPressEvent = self.signal_list_key_press
        signal_layout.addWidget(self.signal_list)
        
        # Add instruction for Enter key
        enter_instruction = QLabel("💡 Chart updates automatically when selecting signals\n🎯 Press Enter or click 'View Chart' to switch to Chart tab")
        enter_instruction.setStyleSheet("color: #007bff; font-style: italic; font-size: 10px; margin: 5px;")
        enter_instruction.setWordWrap(True)
        signal_layout.addWidget(enter_instruction)
        
        layout.addWidget(signal_group, 2, 0, 1, 2)  # Row 2, spans both columns
        
        # Set points - Left column on row 3
        setpoint_group = QGroupBox("📍 Set Point Configuration")
        setpoint_layout = QVBoxLayout(setpoint_group)
        
        # Number of set points
        sp_count_layout = QHBoxLayout()
        sp_count_layout.addWidget(QLabel("Number of set points:"))
        self.setpoint_count = QComboBox()
        self.setpoint_count.addItems(["0", "1", "2", "3", "4", "5"])
        # Only update controls when setpoint count changes, not auto-update chart
        self.setpoint_count.currentTextChanged.connect(self.update_setpoint_controls)
        sp_count_layout.addWidget(self.setpoint_count)
        setpoint_layout.addLayout(sp_count_layout)
        
        # Set point time inputs container
        self.setpoint_inputs_container = QWidget()
        self.setpoint_inputs_layout = QVBoxLayout(self.setpoint_inputs_container)
        setpoint_layout.addWidget(self.setpoint_inputs_container)
        
        # Info label
        info_label = QLabel("💡 Drag set point lines to adjust positions\n⏱️ Default intervals: 2min for minutes, 50s for seconds")
        info_label.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
        info_label.setWordWrap(True)
        setpoint_layout.addWidget(info_label)
        
        layout.addWidget(setpoint_group, 3, 0)  # Row 3, Column 0
        
        # Action buttons - Right column on row 3
        action_group = QGroupBox("🚀 Actions")
        action_layout = QVBoxLayout(action_group)
        
        # Keep generate button but make it auto-trigger
        self.plot_btn = QPushButton("📊 View Chart")
        self.plot_btn.clicked.connect(self.generate_and_show_chart)
        self.plot_btn.setStyleSheet("""
            QPushButton { 
                font-size: 14px; 
                padding: 12px; 
                background-color: #28a745;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        # Show the button for manual chart viewing
        action_layout.addWidget(self.plot_btn)
        
        self.analysis_btn = QPushButton("📋 Show Set Point Analysis")
        self.analysis_btn.clicked.connect(self.show_setpoint_analysis)
        action_layout.addWidget(self.analysis_btn)
        
        self.export_btn = QPushButton("💾 Export Data")
        self.export_btn.clicked.connect(self.export_data)
        action_layout.addWidget(self.export_btn)
        
        self.summary_btn = QPushButton("📄 Show Summary")
        self.summary_btn.clicked.connect(self.show_summary)
        action_layout.addWidget(self.summary_btn)
        
        layout.addWidget(action_group, 3, 1)  # Row 3, Column 1
        
        # Set row stretch to prioritize content
        layout.setRowStretch(1, 1)  # Grouping and Chart sections get more space
        layout.setRowStretch(2, 1)  # Signal selection gets space
        layout.setRowStretch(3, 0)  # Set points and actions are compact
        
        scroll.setWidget(widget)
        return scroll

    def create_preview_panel(self):
        """Create preview panel for setup tab"""
        preview_widget = QWidget()
        layout = QVBoxLayout(preview_widget)
        
        # Preview label
        preview_label = QLabel("📊 Chart Preview")
        preview_label.setFont(QFont("Arial", 12, QFont.Bold))
        preview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(preview_label)
        
        # Preview info
        self.preview_info = QLabel("Generate chart to see preview")
        self.preview_info.setAlignment(Qt.AlignCenter)
        self.preview_info.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(self.preview_info)
        
        # Mini chart container
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        layout.addWidget(self.preview_container)
        
        layout.addStretch()
        return preview_widget

    def create_chart_panel(self):
        chart_widget = QWidget()
        layout = QVBoxLayout(chart_widget)
        layout.setContentsMargins(2, 2, 2, 2)  # Minimal margins
        layout.setSpacing(2)  # Minimal spacing
        
        # Compact controls bar with better visibility
        controls_bar = QWidget()
        controls_bar.setMinimumHeight(40)  # Increase minimum height
        controls_bar.setMaximumHeight(40)  # Set consistent height
        controls_bar.setStyleSheet("QWidget { background-color: #f0f0f0; border-bottom: 1px solid #ddd; }")
        controls_layout = QHBoxLayout(controls_bar)
        controls_layout.setContentsMargins(10, 5, 10, 5)  # Better margins
        
        back_btn = QPushButton("⬅️ Back to Setup")
        back_btn.setMinimumSize(120, 30)  # Larger minimum size
        back_btn.setMaximumSize(120, 30)
        back_btn.setStyleSheet("""
            QPushButton { 
                background-color: #007bff; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        back_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        controls_layout.addWidget(back_btn)
        
        controls_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setMinimumSize(80, 30)  # Larger size
        refresh_btn.setMaximumSize(80, 30)
        refresh_btn.setStyleSheet("""
            QPushButton { 
                background-color: #28a745; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover { background-color: #1e7e34; }
        """)
        refresh_btn.setToolTip("Refresh Chart")
        refresh_btn.clicked.connect(self.plot_chart)
        controls_layout.addWidget(refresh_btn)
        
        analysis_btn = QPushButton("📋 Analysis")
        analysis_btn.setMinimumSize(90, 30)  # Larger size
        analysis_btn.setMaximumSize(90, 30)
        analysis_btn.setStyleSheet("""
            QPushButton { 
                background-color: #ffc107; 
                color: black; 
                border: none; 
                border-radius: 4px; 
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover { background-color: #e0a800; }
        """)
        analysis_btn.setToolTip("Show Analysis")
        analysis_btn.clicked.connect(self.show_setpoint_analysis)
        controls_layout.addWidget(analysis_btn)
        
        export_btn = QPushButton("💾 Export")
        export_btn.setMinimumSize(80, 30)  # Larger size
        export_btn.setMaximumSize(80, 30)
        export_btn.setStyleSheet("""
            QPushButton { 
                background-color: #6f42c1; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover { background-color: #5a2a9d; }
        """)
        export_btn.setToolTip("Export Data")
        export_btn.clicked.connect(self.export_data)
        controls_layout.addWidget(export_btn)
        
        layout.addWidget(controls_bar)
        
        # Chart area (maximize space)
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)  # No margins for chart
        
        # Initial placeholder message
        placeholder = QLabel("Upload data, create groups, and select signals to display chart")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 16px; color: #666666; padding: 50px;")
        self.chart_layout.addWidget(placeholder)
        
        layout.addWidget(self.chart_container)
        
        return chart_widget

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV files (*.csv);;All files (*.*)")
        
        if file_path:
            try:
                self.df = pd.read_csv(file_path)
                
                if "Time" not in self.df.columns:
                    QMessageBox.critical(self, "Error", "Column 'Time' not found in CSV file")
                    return
                
                self.process_data()
                
                filename = os.path.basename(file_path)
                self.file_label.setText(f"Loaded: {filename}")
                self.file_label.setStyleSheet("color: #00ff00; font-weight: bold;")
                
                temp_count = len([c for c in self.df.columns if 'TEMP' in c])
                self.status_bar.showMessage(f"File loaded - {len(self.df)} rows, {temp_count} sensors")
                
                self.update_sensor_list()
                self.update_available_sensors()  # Add this line
                self.update_grouping()
                
                # Stay on current tab - don't auto-switch to chart tab
                self.status_bar.showMessage("Data loaded - Create groups in this tab, then switch to Chart Analysis")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error reading file: {str(e)}")

    def load_sample_data(self):
        sample_file = "data_thermal.csv"
        if os.path.exists(sample_file):
            try:
                self.df = pd.read_csv(sample_file)
                self.process_data()
                self.file_label.setText(f"Loaded: {sample_file}")
                self.file_label.setStyleSheet("color: #00ff00; font-weight: bold;")
                self.status_bar.showMessage(f"Sample data loaded - {len(self.df)} rows")
                self.update_sensor_list()
                self.update_available_sensors()  # Add this line
                self.update_grouping()
                
                # Stay on current tab - don't auto-switch to chart tab
                self.status_bar.showMessage("Sample data loaded - Create groups in this tab, then switch to Chart Analysis")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading sample: {str(e)}")
        else:
            QMessageBox.information(self, "Info", "Sample file 'data_thermal.csv' not found")

    def process_data(self):
        """Process time data and calculate elapsed time"""
        self.df["Time"] = pd.to_datetime(self.df["Time"], format="%Y.%m.%d._%H:%M:%S.%f", errors="coerce")
        self.df = self.df.sort_values("Time").reset_index(drop=True)
        self.df["Elapsed_s"] = (self.df["Time"] - self.df["Time"].iloc[0]).dt.total_seconds()
        self.df["Elapsed_min"] = self.df["Elapsed_s"] / 60

    def update_sensor_list(self):
        if self.df is not None:
            temp_cols = [c for c in self.df.columns if "TEMP" in c]
            self.sensor_list.clear()
            for col in temp_cols:
                self.sensor_list.addItem(col)

    def update_grouping_mode(self):
        # Removed auto mode - always use manual
        self.update_signal_list()

    def update_grouping(self):
        if self.df is None:
            return
        
        # Don't create any automatic groups - user must create manually
        # Always use manual groups only
        self.groups = self.manual_groups.copy()
        self.update_signal_list()

    def update_available_sensors(self):
        """Update sensor list to show only unassigned sensors"""
        if self.df is None:
            return
        
        # Get all temperature sensors
        temp_columns = [col for col in self.df.columns if 'temp' in col.lower() and col != 'Time']
        
        # Get already assigned sensors
        assigned_sensors = set()
        for group_sensors in self.manual_groups.values():
            assigned_sensors.update(group_sensors)
        
        # Show only unassigned sensors
        self.sensor_list.clear()
        for col in temp_columns:
            if col not in assigned_sensors:
                self.sensor_list.addItem(col)
            
        temp_cols = [c for c in self.df.columns if "TEMP" in c]
        self.groups = {"Vent": [], "Head": [], "Outside": []}
        
        for col in temp_cols:
            series = self.df[col].dropna()
            if len(series) < 5:
                continue
                
            mean_temp = series.mean()
            delta_temp = series.max() - series.min()
            
            if mean_temp < 20 and delta_temp > 20:
                self.groups["Vent"].append(col)
            elif 20 <= mean_temp < 35 and delta_temp > 10:
                self.groups["Head"].append(col)
            elif mean_temp > 35 and delta_temp < 5:
                self.groups["Outside"].append(col)
        
        # Create group averages
        for name, cols in self.groups.items():
            if len(cols) > 0:
                valid_cols = [c for c in cols if c in self.df.columns]
                if valid_cols:
                    self.df[name] = self.df[valid_cols].mean(axis=1)

    def add_manual_group(self):
        group_name = self.group_name_input.text().strip()
        selected_items = self.sensor_list.selectedItems()
        
        if not group_name or not selected_items:
            QMessageBox.warning(self, "Warning", "Please enter group name and select sensors")
            return
        
        selected_sensors = [item.text() for item in selected_items]
        self.manual_groups[group_name] = selected_sensors
        self.groups[group_name] = selected_sensors
        
        # Create group average
        self.df[group_name] = self.df[selected_sensors].mean(axis=1)
        
        self.update_groups_display()
        self.update_available_sensors()  # Update to remove assigned sensors
        self.update_signal_list()
        self.group_name_input.clear()
        self.status_bar.showMessage(f"Added group '{group_name}' with {len(selected_sensors)} sensors")
        
        # Don't auto-update chart - let user select signals first

    def remove_manual_group(self):
        if not self.manual_groups:
            QMessageBox.information(self, "Info", "No groups to remove")
            return
        
        # Remove last group (simplified)
        if self.manual_groups:
            last_group = list(self.manual_groups.keys())[-1]
            del self.manual_groups[last_group]
            if last_group in self.groups:
                del self.groups[last_group]
            if last_group in self.df.columns:
                self.df.drop(columns=[last_group], inplace=True)
            self.update_groups_display()
            self.update_available_sensors()  # Update to show sensors again
            self.update_signal_list()
            self.status_bar.showMessage(f"Removed group '{last_group}'")
            
            # Don't auto-update chart - let user select signals first

    def update_groups_display(self):
        text = ""
        if self.manual_groups:
            for name, sensors in self.manual_groups.items():
                text += f"• {name}: {len(sensors)} sensors\n"
        else:
            text = "No manual groups created"
        self.groups_display.setText(text)

    def update_signal_list(self):
        """Update signal selection list"""
        if self.df is None:
            return
        
        self.signal_list.clear()
        
        # Add manual groups (since we removed auto mode)
        for group_name in self.manual_groups.keys():
            if group_name in self.df.columns and len(self.manual_groups[group_name]) > 0:
                self.signal_list.addItem(f"{group_name} ({len(self.manual_groups[group_name])} sensors)")
        
        # Add speed if available
        speed_col = "Dyno_Speed_[dyno_speed]"
        if speed_col in self.df.columns:
            self.signal_list.addItem("Speed [kph]")
        
        # Don't select anything by default - let user choose
        # User will select signals manually to generate chart

    def update_setpoint_controls(self):
        # Clear existing inputs
        for i in reversed(range(self.setpoint_inputs_layout.count())):
            self.setpoint_inputs_layout.itemAt(i).widget().setParent(None)
        
        # Initialize positions and input widgets
        self.setpoint_positions = []
        self.setpoint_inputs = []
        num_points = int(self.setpoint_count.currentText())
        
        if num_points > 0 and self.df is not None:
            time_col = "Elapsed_min" if self.time_minute.isChecked() else "Elapsed_s"
            time_unit = "min" if self.time_minute.isChecked() else "s"
            max_time = float(self.df[time_col].max())
            
            point_labels = ['A', 'B', 'C', 'D', 'E']
            
            # Create input boxes for each set point
            for i in range(num_points):
                # Custom smaller intervals based on time unit
                if time_unit == "min":
                    # For minutes: start at 2min intervals
                    pos = (i + 1) * 2.0
                else:
                    # For seconds: start at 50s intervals  
                    pos = (i + 1) * 50.0
                
                # Ensure we don't exceed max_time
                if pos > max_time:
                    pos = max_time * (i + 1) / (num_points + 1)
                    
                self.setpoint_positions.append(pos)
                
                # Create input layout
                input_layout = QHBoxLayout()
                label = QLabel(f"Set Point {point_labels[i]}:")
                label.setMinimumWidth(80)
                input_layout.addWidget(label)
                
                # Time input
                time_input = QLineEdit()
                time_input.setText(f"{pos:.1f}")
                time_input.setMaximumWidth(80)
                time_input.setPlaceholderText(f"Time ({time_unit})")
                time_input.editingFinished.connect(lambda idx=i: self.update_setpoint_from_input(idx))
                input_layout.addWidget(time_input)
                
                input_layout.addWidget(QLabel(time_unit))
                input_layout.addStretch()
                
                # Add to container
                input_widget = QWidget()
                input_widget.setLayout(input_layout)
                self.setpoint_inputs_layout.addWidget(input_widget)
                self.setpoint_inputs.append(time_input)
        
        self.status_bar.showMessage(f"Set {num_points} set points - drag them on chart to adjust")
        # Auto-update chart if it exists
        self.auto_update_chart()

    def update_setpoint_from_input(self, index):
        """Update set point position from input box"""
        if not hasattr(self, 'setpoint_inputs') or index >= len(self.setpoint_inputs):
            return
        
        try:
            new_time = float(self.setpoint_inputs[index].text())
            time_col = "Elapsed_min" if self.time_minute.isChecked() else "Elapsed_s"
            max_time = self.df[time_col].max()
            
            # Constrain to valid range
            new_time = max(0, min(max_time, new_time))
            self.setpoint_inputs[index].setText(f"{new_time:.1f}")
            
            # Update internal position
            if hasattr(self, 'setpoint_positions') and index < len(self.setpoint_positions):
                self.setpoint_positions[index] = new_time
            
            # Update chart if visible
            self.auto_update_chart()
            
        except ValueError:
            # Reset to previous value if invalid input
            if hasattr(self, 'setpoint_positions') and index < len(self.setpoint_positions):
                self.setpoint_inputs[index].setText(f"{self.setpoint_positions[index]:.1f}")

    def get_selected_signals(self):
        """Get list of selected signals to plot"""
        selected_signals = []
        
        for item in self.signal_list.selectedItems():
            signal_text = item.text()
            if "Speed" in signal_text:
                selected_signals.append("Dyno_Speed_[dyno_speed]")
            else:
                # Extract group name
                group_name = signal_text.split(" (")[0]
                if group_name in self.manual_groups:  # Use manual_groups instead
                    selected_signals.append(group_name)
        
        return selected_signals

    def on_signal_selection_changed(self):
        """Handle signal selection changes - create/update chart WITHOUT switching tabs"""
        if self._updating:
            return  # Prevent recursion
            
        if hasattr(self, 'df') and self.df is not None:
            self._updating = True
            try:
                signals = self.get_selected_signals()
                if len(signals) > 0:
                    # Create or update chart but DON'T switch tabs
                    if not hasattr(self, 'fig') or self.fig is None:
                        self.generate_chart_only()  # New method that doesn't switch tabs
                    else:
                        self.plot_chart()
                else:
                    # Clear chart if no signals selected
                    if hasattr(self, 'fig') and self.fig is not None:
                        self.clear_chart_area()
            finally:
                self._updating = False

    def clear_chart_area(self):
        """Clear chart area when no signals selected"""
        if hasattr(self, 'chart_layout'):
            # Clear previous plot
            for i in reversed(range(self.chart_layout.count())):
                widget = self.chart_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            
            # Add placeholder message
            placeholder = QLabel("Create groups and select signals to display chart")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("font-size: 16px; color: #666666; padding: 50px;")
            self.chart_layout.addWidget(placeholder)
            
            # Reset chart-related attributes
            self.fig = None
            self.canvas = None
            self.status_bar.showMessage("No signals selected")

    def auto_generate_initial_chart(self):
        """Auto-generate chart when first loading data - ONLY if signals are selected"""
        if hasattr(self, 'df') and self.df is not None:
            # Only generate if user has actively selected signals
            signals = self.get_selected_signals()
            if len(signals) > 0:
                self.generate_and_show_chart()

    def auto_update_chart(self):
        """Auto-update chart when settings change (NOT signal selection)"""
        if self._updating:
            return  # Prevent recursion
            
        if (hasattr(self, 'df') and self.df is not None and 
            hasattr(self, 'fig') and self.fig is not None and
            len(self.get_selected_signals()) > 0):
            # Only update existing chart, don't create new one
            self._updating = True
            try:
                self.plot_chart()
            finally:
                self._updating = False

    def generate_and_show_chart(self):
        """Generate chart and switch to chart tab"""
        self.plot_chart()
        if hasattr(self, 'fig') and self.fig is not None:
            self.tab_widget.setCurrentIndex(1)  # Switch to chart tab

    def generate_chart_only(self):
        """Generate chart WITHOUT switching tabs"""
        self.plot_chart()
        # No tab switching here - chart updates in background

    def plot_chart(self):
        if self.df is None:
            QMessageBox.warning(self, "Warning", "Please upload a CSV file first")
            return
        
        # Get selected signals
        signals_to_plot = self.get_selected_signals()
        if not signals_to_plot:
            QMessageBox.warning(self, "Warning", "Please select at least one signal to plot")
            return
        
        self.update_setpoint_controls()
        
        # Clear previous plot
        for i in reversed(range(self.chart_layout.count())):
            self.chart_layout.itemAt(i).widget().setParent(None)
        
        # Create matplotlib figure with optimized size
        self.fig = Figure(figsize=(16, 9), dpi=100, facecolor='white')
        self.canvas = FigureCanvas(self.fig)
        
        # Compact navigation toolbar
        toolbar = NavigationToolbar(self.canvas, self)
        toolbar.setMaximumHeight(30)
        
        self.chart_layout.addWidget(toolbar)
        self.chart_layout.addWidget(self.canvas)
        
        # Variables for interactive set point dragging and tooltips
        self.dragging_setpoint = None
        self.setpoint_lines = {}
        self.setpoint_texts = {}
        self.setpoint_tooltips = {}
        self.setpoint_markers = {}  # Add this for markers
        self.press_event = None
        self.tooltip = None  # Initialize tooltip for hover
        self.current_tooltip = None  # For new tooltip system
        
        # Connect mouse events for dragging and tooltips
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        
        # Plot data
        ax1 = self.fig.add_subplot(111)
        
        # Get time data
        time_col = "Elapsed_min" if self.time_minute.isChecked() else "Elapsed_s"
        time_unit = "min" if self.time_minute.isChecked() else "s"
        
        # Colors for lines (thinner lines)
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        color_idx = 0
        
        # Track speed separately
        speed_col = "Dyno_Speed_[dyno_speed]"
        has_speed = speed_col in signals_to_plot and speed_col in self.df.columns
        
        # Plot temperature signals with thinner lines
        plotted_groups = []
        for sig in signals_to_plot:
            if sig == speed_col:
                continue
            
            if sig in self.df.columns:
                sensor_count = len(self.manual_groups.get(sig, []))
                label = sig  # Only show signal name, no sensor count
                ax1.plot(self.df[time_col], self.df[sig], 
                        label=label, 
                        color=colors[color_idx % len(colors)], 
                        linewidth=1.5)  # Thinner lines
                plotted_groups.append(sig)
                color_idx += 1
        
        # Plot speed on secondary axis with thinner line
        if has_speed:
            ax2 = ax1.twinx()
            ax2.plot(self.df[time_col], self.df[speed_col], 
                    label="Speed", color="darkblue", linewidth=2)  # Thinner
            ax2.tick_params(axis='y', labelcolor="darkblue")
            
            if self.y_from_zero.isChecked():
                ax2.set_ylim(bottom=0)
        
        # Styling with proper title positioning
        ax1.set_xlabel(f"Time ({time_unit})", fontweight='bold')
        ax1.set_ylabel("Temperature [°C]", fontweight='bold')
        
        # Set chart title with adequate spacing
        title_text = self.title_input.text() or "Thermal Analysis Chart"
        ax1.set_title(title_text, fontweight='bold', fontsize=14, pad=15)
        
        # Set axes to start from origin (0,0) with minimal spacing
        if self.y_from_zero.isChecked():
            ax1.set_ylim(bottom=0)
        
        # Set X axis to start from 0 with minimal margin
        ax1.set_xlim(left=0, right=self.df[time_col].max())
        
        # Enhanced axes styling with arrows and triangle markers
        # Style the spines (axis lines)
        ax1.spines['left'].set_linewidth(1.2)
        ax1.spines['left'].set_color('black')
        ax1.spines['bottom'].set_linewidth(1.2)
        ax1.spines['bottom'].set_color('black')
        
        # Hide top and right spines for cleaner look (unless speed axis exists)
        if not has_speed:
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
        else:
            ax1.spines['top'].set_visible(False)
            # Keep right spine visible for speed axis
        
        # Add arrow markers at axis ends (always visible)
        # Get current axis limits
        x_min, x_max = ax1.get_xlim()
        y_min, y_max = ax1.get_ylim()
        
        # Calculate arrow positions at axis ends using axes coordinates (fixed position)
        
        # X-axis arrow (at right end of X-axis) - fixed at axes position
        ax1.annotate('', xy=(1.0, 0), xytext=(0.98, 0),
                    xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=dict(arrowstyle='-|>', color='black', lw=1.5),
                    annotation_clip=False)
        
        # Y-axis arrow (at top end of Y-axis) - fixed at axes position
        ax1.annotate('', xy=(0, 1.0), xytext=(0, 0.98),
                    xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=dict(arrowstyle='-|>', color='black', lw=1.5),
                    annotation_clip=False)
        
        # Normal tick marks
        ax1.tick_params(axis='x', direction='out', length=5, width=1, 
                       which='major', pad=6, color='black')
        ax1.tick_params(axis='y', direction='out', length=5, width=1, 
                       which='major', pad=6, color='black')
        
        # Style secondary axis if it exists
        if has_speed:
            ax2.set_ylabel("Speed [RPM]", fontweight='bold', color='darkblue')
            ax2.tick_params(axis='y', labelcolor='darkblue', direction='out', 
                           length=5, width=1, which='major', pad=6, color='darkblue')
            
            # Style right spine
            ax2.spines['right'].set_linewidth(1.2)
            ax2.spines['right'].set_color('darkblue')
            
            # Add arrow to right Y-axis (speed) - fixed at axes position
            ax2.annotate('', xy=(1.0, 1.0), xytext=(1.0, 0.98),
                        xycoords='axes fraction', textcoords='axes fraction',
                        arrowprops=dict(arrowstyle='-|>', color='darkblue', lw=1.5),
                        annotation_clip=False)
        
        # Remove duplicate X-axis arrow (already added above)
        
        # Add grid with smart step calculation
        max_time = self.df[time_col].max()
        
        if time_unit == "min":
            # For minutes: step of 2 minutes
            step = 2
        else:
            # For seconds: step of 50 seconds
            step = 50
        
        grid_lines = list(range(0, int(max_time) + step, step))
        ax1.set_xticks(grid_lines)
        
        # Rotate labels for seconds to prevent overlap
        if time_unit == "s":
            ax1.tick_params(axis='x', rotation=45)
        
        ax1.grid(True, alpha=0.3)
        
        # Add set points with A, B, C labels
        num_points = int(self.setpoint_count.currentText())
        if num_points > 0:
            self.marker_positions = []
            self.setpoint_lines = {}
            self.setpoint_texts = {}
            point_colors = ['red', 'green', 'blue', 'purple', 'orange']
            point_labels = ['A', 'B', 'C', 'D', 'E']
            
            # Use predefined positions if available, otherwise create defaults
            if hasattr(self, 'setpoint_positions') and len(self.setpoint_positions) >= num_points:
                positions = self.setpoint_positions[:num_points]
            else:
                # Create default positions
                max_time = self.df[time_col].max()
                positions = [(i + 1) * max_time / (num_points + 1) for i in range(num_points)]
            
            for i in range(num_points):
                pos = positions[i]
                self.marker_positions.append(pos)
                color = point_colors[i % len(point_colors)]
                label = point_labels[i % len(point_labels)]
                
                # Store reference to the line for interactive dragging
                line = ax1.axvline(x=pos, color=color, linestyle='--', alpha=0.8, linewidth=2, picker=True)
                line.set_pickradius(15)  # Make line easier to click
                
                # Store line reference with label key
                self.setpoint_lines[label] = line
                
                # Add time display below x-axis  
                time_text = ax1.annotate(f'{pos:.1f}{time_unit}', 
                           xy=(pos, ax1.get_ylim()[0]), 
                           xytext=(0, -25), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9),
                           color='black', fontsize=10,
                           ha='center', va='top')
                self.setpoint_texts[f'{label}_time'] = time_text
                
                # Add tooltips for each signal at this set point
                self.add_setpoint_tooltips(ax1, ax2 if has_speed else None, pos, label, signals_to_plot, time_col, i)
            
        self.signals_to_plot = signals_to_plot
        # Store axis references for tooltip updates
        self.ax1 = ax1
        self.ax2 = ax2 if has_speed else None
        
        # Legend - positioned to minimize chart obstruction
        if plotted_groups:
            # Create combined legend for both temperature and speed if available
            lines1, labels1 = ax1.get_legend_handles_labels()
            if has_speed:
                lines2, labels2 = ax2.get_legend_handles_labels()
                # Position legend at bottom with horizontal layout
                ax1.legend(lines1 + lines2, labels1 + labels2, 
                          loc='upper center', bbox_to_anchor=(0.5, -0.08), 
                          ncol=min(len(labels1 + labels2), 6), 
                          frameon=True, fancybox=True, shadow=False, fontsize=9)
            else:
                # Position legend at bottom with horizontal layout
                ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08), 
                          ncol=min(len(labels1), 6), 
                          frameon=True, fancybox=True, shadow=False, fontsize=9)
        
        # Optimized chart layout for maximum display space
        ax1.margins(x=0.005, y=0.01)  # Minimal margins
        if has_speed:
            ax2.margins(x=0.005, y=0.01)
        
        # Set tight layout with optimized padding
        self.fig.tight_layout(pad=1.0)
        
        # Maximize chart area - adjust subplot parameters with more top space for title
        self.fig.subplots_adjust(left=0.06, right=0.94, top=0.90, bottom=0.18)
        
        self.canvas.draw()
        
        self.status_bar.showMessage(f"Chart generated with {len(plotted_groups)} temperature groups" + 
                                   (" + speed" if has_speed else ""))

    def get_signal_color(self, signal, signals_to_plot):
        """Get the color for a signal based on its position in the plot"""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        if "Speed" in signal or "speed" in signal:
            return 'darkblue'
        else:
            # Find position of signal among temperature signals only
            temp_signals = [s for s in signals_to_plot if not ("Speed" in s or "speed" in s)]
            try:
                temp_index = temp_signals.index(signal)
                return colors[temp_index % len(colors)]
            except ValueError:
                return colors[0]  # Fallback

    def add_setpoint_tooltips(self, ax1, ax2, pos, label, signals_to_plot, time_col, setpoint_index):
        """Add tooltips for each signal at set point position with smart positioning"""
        # Find closest data point to set point position
        idx = (self.df[time_col] - pos).abs().idxmin()
        x_val = self.df[time_col].iloc[idx]
        
        # Colors for different signals (same as plot colors)
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        # Get axis limits for bounds checking
        x_min, x_max = ax1.get_xlim()
        y_min, y_max = ax1.get_ylim()
        
        # Smart positioning: determine which side of chart we're on
        x_ratio = (x_val - x_min) / (x_max - x_min)  # 0 = left edge, 1 = right edge
        
        # Collect all y values for smart vertical positioning
        y_values = []
        for signal in signals_to_plot:
            if signal in self.df.columns:
                y_val = self.df[signal].iloc[idx]
                is_speed = "Speed" in signal or "speed" in signal
                # Normalize y values to [0,1] range for comparison
                if is_speed and ax2:
                    y2_min, y2_max = ax2.get_ylim()
                    y_norm = (y_val - y2_min) / (y2_max - y2_min)
                else:
                    y_norm = (y_val - y_min) / (y_max - y_min)
                y_values.append((signal, y_val, is_speed, y_norm))
        
        # Sort by normalized y position for smart stacking
        y_values.sort(key=lambda x: x[3])
        
        for j, (signal, y_val, is_speed, y_norm) in enumerate(y_values):
            # Determine which axis to use
            if is_speed and ax2:
                axis_ref = ax2
            else:
                axis_ref = ax1
            
            # Get actual line color for this signal
            line_color = self.get_signal_color(signal, signals_to_plot)
            
            # Create small marker at intersection point with same color as line
            marker = axis_ref.plot(x_val, y_val, 'o', 
                                 color=line_color, 
                                 markersize=5, 
                                 markeredgecolor='white', 
                                 markeredgewidth=1,
                                 zorder=10)[0]
            
            # Store marker for later removal/update
            if not hasattr(self, 'setpoint_markers'):
                self.setpoint_markers = {}
            if label not in self.setpoint_markers:
                self.setpoint_markers[label] = []
            self.setpoint_markers[label].append(marker)
            
            # Create tooltip text - only value, no signal name
            if is_speed:
                tooltip_text = f"{y_val:.0f} RPM"
            else:
                tooltip_text = f"{y_val:.1f}°C"
            
            # Smart positioning logic
            # Horizontal: prefer right side unless near right edge
            if x_ratio > 0.7:  # Near right edge
                h_offset = -25 - (j * 5)  # Closer to marker, smaller stagger
                h_align = 'right'
            else:  # Left side or center
                h_offset = 25 + (j * 5)   # Closer to marker, smaller stagger
                h_align = 'left'
            
            # Vertical: stack based on y position and avoid edges
            if y_norm > 0.8:  # Near top
                v_offset = -15 - (j * 8)  # Closer and smaller stagger
                v_align = 'top'
            elif y_norm < 0.2:  # Near bottom
                v_offset = 15 + (j * 8)   # Closer and smaller stagger
                v_align = 'bottom'
            else:  # Middle area
                v_offset = 8 + (j * 10)   # Closer stagger
                v_align = 'bottom'
            
            # Create tooltip annotation without arrow - just positioned near marker
            tooltip = axis_ref.annotate(tooltip_text,
                                      xy=(x_val, y_val),
                                      xytext=(h_offset, v_offset), 
                                      textcoords='offset points',
                                      bbox=dict(boxstyle='round,pad=0.3', 
                                              facecolor='white', 
                                              alpha=0.9,
                                              edgecolor=line_color,
                                              linewidth=1.5),
                                      fontsize=9,
                                      fontweight='bold',
                                      ha=h_align,
                                      va=v_align,
                                      zorder=15)
            
            # Store tooltip for later removal/update
            if not hasattr(self, 'setpoint_tooltips'):
                self.setpoint_tooltips = {}
            if label not in self.setpoint_tooltips:
                self.setpoint_tooltips[label] = []
            self.setpoint_tooltips[label].append(tooltip)

    def update_setpoint_tooltips(self, new_x, label, time_col):
        """Update tooltip positions and values when set point moves"""
        if not hasattr(self, 'df') or self.df is None:
            return
            
        # Find new data point
        idx = (self.df[time_col] - new_x).abs().idxmin()
        x_val = self.df[time_col].iloc[idx]
        
        # Colors for different signals  
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        # Get axis limits for bounds checking
        x_min, x_max = self.ax1.get_xlim()
        y_min, y_max = self.ax1.get_ylim()
        
        # Smart positioning: determine which side of chart we're on
        x_ratio = (x_val - x_min) / (x_max - x_min)  # 0 = left edge, 1 = right edge
        
        # Remove old tooltips and markers for this setpoint
        if hasattr(self, 'setpoint_tooltips') and label in self.setpoint_tooltips:
            for tooltip in self.setpoint_tooltips[label]:
                tooltip.remove()
            del self.setpoint_tooltips[label]
            
        if hasattr(self, 'setpoint_markers') and label in self.setpoint_markers:
            for marker in self.setpoint_markers[label]:
                marker.remove()
            del self.setpoint_markers[label]
        
        # Get current signals being plotted
        signals = getattr(self, 'signals_to_plot', [])
        
        # Collect all y values for smart vertical positioning
        y_values = []
        for signal in signals:
            if signal in self.df.columns:
                y_val = self.df[signal].iloc[idx]
                is_speed = "Speed" in signal or "speed" in signal
                # Normalize y values to [0,1] range for comparison
                ax2 = getattr(self, 'ax2', None)
                if is_speed and ax2:
                    y2_min, y2_max = ax2.get_ylim()
                    y_norm = (y_val - y2_min) / (y2_max - y2_min)
                else:
                    y_norm = (y_val - y_min) / (y_max - y_min)
                y_values.append((signal, y_val, is_speed, y_norm))
        
        # Sort by normalized y position for smart stacking
        y_values.sort(key=lambda x: x[3])
        
        # Re-create tooltips at new position with smart positioning
        if hasattr(self, 'ax1'):
            ax2 = getattr(self, 'ax2', None)
            
            for j, (signal, y_val, is_speed, y_norm) in enumerate(y_values):
                # Determine which axis to use
                if is_speed and ax2:
                    axis_ref = ax2
                else:
                    axis_ref = self.ax1
                
                # Get actual line color for this signal
                line_color = self.get_signal_color(signal, signals)
                
                # Create small marker at intersection point with same color as line
                marker = axis_ref.plot(x_val, y_val, 'o', 
                                     color=line_color, 
                                     markersize=5, 
                                     markeredgecolor='white', 
                                     markeredgewidth=1,
                                     zorder=10)[0]
                
                # Store marker for later removal/update
                if not hasattr(self, 'setpoint_markers'):
                    self.setpoint_markers = {}
                if label not in self.setpoint_markers:
                    self.setpoint_markers[label] = []
                self.setpoint_markers[label].append(marker)
                
                # Create tooltip text - only value, no signal name
                if is_speed:
                    tooltip_text = f"{y_val:.0f} RPM"
                else:
                    tooltip_text = f"{y_val:.1f}°C"
                
                # Smart positioning logic (same as add_setpoint_tooltips)
                # Horizontal: prefer right side unless near right edge
                if x_ratio > 0.7:  # Near right edge
                    h_offset = -25 - (j * 5)  # Closer to marker, smaller stagger
                    h_align = 'right'
                else:  # Left side or center
                    h_offset = 25 + (j * 5)   # Closer to marker, smaller stagger
                    h_align = 'left'
                
                # Vertical: stack based on y position and avoid edges
                if y_norm > 0.8:  # Near top
                    v_offset = -15 - (j * 8)  # Closer and smaller stagger
                    v_align = 'top'
                elif y_norm < 0.2:  # Near bottom
                    v_offset = 15 + (j * 8)   # Closer and smaller stagger
                    v_align = 'bottom'
                else:  # Middle area
                    v_offset = 8 + (j * 10)   # Closer stagger
                    v_align = 'bottom'
                
                # Create tooltip annotation without arrow - just positioned near marker
                tooltip = axis_ref.annotate(tooltip_text,
                                          xy=(x_val, y_val),
                                          xytext=(h_offset, v_offset), 
                                          textcoords='offset points',
                                          bbox=dict(boxstyle='round,pad=0.3', 
                                                  facecolor='white', 
                                                  alpha=0.9,
                                                  edgecolor=line_color,
                                                  linewidth=1.5),
                                          fontsize=9,
                                          fontweight='bold',
                                          ha=h_align,
                                          va=v_align,
                                          zorder=15)
                
                # Store tooltip for later removal/update
                if not hasattr(self, 'setpoint_tooltips'):
                    self.setpoint_tooltips = {}
                if label not in self.setpoint_tooltips:
                    self.setpoint_tooltips[label] = []
                self.setpoint_tooltips[label].append(tooltip)

    def on_press(self, event):
        """Handle mouse press events for set point dragging"""
        if event.inaxes is None or not hasattr(self, 'setpoint_lines'):
            return
        
        # Check if we clicked on a set point line
        for key, line in self.setpoint_lines.items():
            if line is not None and line.contains(event)[0]:
                self.dragging_setpoint = key
                self.press_event = event
                # Change cursor to indicate dragging (using widget cursor)
                self.canvas.widget().setCursor(Qt.SizeHorCursor)
                break

    def on_motion(self, event):
        """Handle mouse motion events for set point dragging and tooltips"""
        if event.inaxes is None:
            return
        
        # Handle set point dragging
        if (self.dragging_setpoint is not None and hasattr(self, 'setpoint_lines') and self.press_event is not None):
            line = self.setpoint_lines[self.dragging_setpoint]
            if line is not None:
                # Update line position
                new_x = event.xdata
                if new_x is not None:
                    # Constrain to data range
                    time_col = "Elapsed_min" if self.time_minute.isChecked() else "Elapsed_s"
                    time_unit = "min" if self.time_minute.isChecked() else "s"
                    if hasattr(self, 'df') and self.df is not None:
                        min_time = 0
                        max_time = self.df[time_col].max()
                        new_x = max(min_time, min(max_time, new_x))
                    
                    # Update line position
                    line.set_xdata([new_x, new_x])
                    
                    # Update setpoint_positions array and input field
                    if hasattr(self, 'setpoint_positions'):
                        # Extract setpoint index from dragging_setpoint (e.g., "Setpoint 1" -> index 0)
                        try:
                            sp_index = int(self.dragging_setpoint.split()[-1]) - 1
                            if 0 <= sp_index < len(self.setpoint_positions):
                                self.setpoint_positions[sp_index] = new_x
                                
                                # Also update marker_positions for analysis consistency
                                if hasattr(self, 'marker_positions') and sp_index < len(self.marker_positions):
                                    self.marker_positions[sp_index] = new_x
                                
                                # Update corresponding input field
                                if hasattr(self, 'setpoint_inputs') and sp_index < len(self.setpoint_inputs):
                                    self.setpoint_inputs[sp_index].setText(f"{new_x:.1f}")
                                
                                # Emit signal to notify analysis dialog
                                self.setpoint_changed.emit()
                        except (ValueError, IndexError):
                            pass  # Ignore if setpoint name doesn't follow expected format
                    
                    # Update time display
                    time_key = f'{self.dragging_setpoint}_time'
                    if time_key in self.setpoint_texts:
                        time_obj = self.setpoint_texts[time_key]
                        ax = line.axes
                        time_obj.xy = (new_x, ax.get_ylim()[0])
                        time_obj.set_text(f'{new_x:.1f}{time_unit}')
                    
                    # Update tooltips for this set point
                    self.update_setpoint_tooltips(new_x, self.dragging_setpoint, time_col)
                    
                    self.canvas.draw_idle()
        
        # Show tooltips when not dragging - not needed anymore since we have fixed tooltips
        # else:
        #     self.show_tooltip(event)

    def show_tooltip(self, event):
        """Show tooltip with values at intersection points"""
        if not hasattr(self, 'df') or self.df is None or event.inaxes is None:
            return
        
        # Only show tooltip when hovering near setpoint lines
        if hasattr(self, 'setpoint_lines'):
            for label, line in self.setpoint_lines.items():
                setpoint_x = line.get_xdata()[0]
                
                # Check if cursor is near this setpoint line (within 2% of x-range)
                x_range = event.inaxes.get_xlim()[1] - event.inaxes.get_xlim()[0]
                if abs(event.xdata - setpoint_x) < x_range * 0.02:
                    
                    # Find values at this setpoint for all signals
                    time_col = "Elapsed_min" if self.time_minute.isChecked() else "Elapsed_s"
                    time_unit = "min" if self.time_minute.isChecked() else "s"
                    
                    # Find closest data point to setpoint
                    time_diff = (self.df[time_col] - setpoint_x).abs()
                    closest_idx = time_diff.idxmin()
                    actual_time = self.df.loc[closest_idx, time_col]
                    
                    # Build tooltip text with values at intersection
                    tooltip_lines = [f"Set Point {label}: {actual_time:.1f}{time_unit}"]
                    
                    # Add temperature values for selected signals
                    if hasattr(self, 'signals_to_plot'):
                        for signal in self.signals_to_plot:
                            if signal in self.df.columns and 'Speed' not in signal:
                                value = self.df.loc[closest_idx, signal]
                                tooltip_lines.append(f"{signal}: {value:.1f}°C")
                    
                    # Add speed if available and selected
                    speed_col = "Dyno_Speed_[dyno_speed]"
                    if speed_col in self.signals_to_plot and speed_col in self.df.columns:
                        speed_value = self.df.loc[closest_idx, speed_col]
                        tooltip_lines.append(f"Speed: {speed_value:.0f} RPM")
                    
                    # Create/update tooltip
                    tooltip_text = "\n".join(tooltip_lines)
                    
                    # Remove old tooltip if exists
                    if hasattr(self, 'current_tooltip') and self.current_tooltip:
                        self.current_tooltip.remove()
                    
                    # Create new tooltip at intersection point
                    y_values = []
                    for signal in self.signals_to_plot:
                        if signal in self.df.columns and 'Speed' not in signal:
                            y_values.append(self.df.loc[closest_idx, signal])
                    
                    if y_values:
                        avg_y = sum(y_values) / len(y_values)
                        self.current_tooltip = event.inaxes.annotate(
                            tooltip_text,
                            xy=(setpoint_x, avg_y),
                            xytext=(20, 20), textcoords='offset points',
                            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", 
                                    edgecolor="orange", alpha=0.9),
                            fontsize=9, ha='left',
                            arrowprops=dict(arrowstyle='->', color='orange', lw=1)
                        )
                        self.canvas.draw_idle()
                    return
        
        # Hide tooltip if not near any setpoint
        if hasattr(self, 'current_tooltip') and self.current_tooltip:
            self.current_tooltip.remove()
            self.current_tooltip = None
            self.canvas.draw_idle()

    def on_release(self, event):
        """Handle mouse release events for set point dragging"""
        if self.dragging_setpoint is not None:
            self.dragging_setpoint = None
            self.press_event = None
            self.canvas.widget().setCursor(Qt.ArrowCursor)
            
            # Update marker positions for analysis
            if hasattr(self, 'marker_positions'):
                self.marker_positions = []
                for key, line in self.setpoint_lines.items():
                    if not key.endswith('_time'):  # Skip time text keys
                        pos = line.get_xdata()[0]
                        self.marker_positions.append(pos)

    def show_setpoint_analysis(self):
        # Close existing analysis dialog if open
        if hasattr(self, 'analysis_dialog') and self.analysis_dialog:
            self.analysis_dialog.close()
        
        # Use current setpoint positions (updated by dragging) or fallback to marker_positions
        current_positions = []
        if hasattr(self, 'setpoint_positions') and self.setpoint_positions:
            current_positions = self.setpoint_positions
        elif hasattr(self, 'marker_positions') and self.marker_positions:
            current_positions = self.marker_positions
        else:
            QMessageBox.information(self, "Info", "Please generate chart with set points first")
            return
        
        if not hasattr(self, 'df') or self.df is None:
            QMessageBox.warning(self, "Warning", "No data available for analysis")
            return
        
        # Create real-time analysis dialog
        self.analysis_dialog = SetpointAnalysisDialog(self, current_positions)
        self.analysis_dialog.show()
        
        # Connect signal for real-time updates
        self.setpoint_changed.connect(self.analysis_dialog.update_analysis)


class SetpointAnalysisDialog(QWidget):
    def __init__(self, parent, initial_positions):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("📋 Set Point Analysis - Real-time")
        self.setGeometry(200, 200, 800, 600)
        self.setWindowModality(Qt.ApplicationModal)
        
        self.layout = QVBoxLayout(self)
        
        # Title
        self.title = QLabel("Set Point Values Analysis (Live Update)")
        self.title.setFont(QFont("Arial", 14, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title)
        
        # Status label
        self.status_label = QLabel("📊 Live updating when you drag setpoints...")
        self.status_label.setStyleSheet("color: #28a745; font-style: italic; padding: 5px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)
        
        # Table container
        self.table = QTableWidget()
        self.layout.addWidget(self.table)
        
        # Time difference label container
        self.diff_label = QLabel()
        self.layout.addWidget(self.diff_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        self.layout.addWidget(close_btn)
        
        # Initial data load
        self.update_analysis()
    
    def update_analysis(self):
        """Update analysis data in real-time"""
        if not hasattr(self.parent, 'df') or self.parent.df is None:
            return
        
        # Get current positions
        current_positions = []
        if hasattr(self.parent, 'setpoint_positions') and self.parent.setpoint_positions:
            current_positions = self.parent.setpoint_positions
        elif hasattr(self.parent, 'marker_positions') and self.parent.marker_positions:
            current_positions = self.parent.marker_positions
        
        if not current_positions:
            return
        
        # Get data
        time_col = "Elapsed_min" if self.parent.time_minute.isChecked() else "Elapsed_s"
        time_unit = "min" if self.parent.time_minute.isChecked() else "s"
        
        # Get current signals being plotted
        current_signals = getattr(self.parent, 'signals_to_plot', [])
        available_signals = [sig for sig in current_signals if sig in self.parent.df.columns]
        
        # Setup table
        headers = ["Set Point", "Time"] + available_signals
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(current_positions))
        
        # Fill data using current positions
        for i, pos in enumerate(current_positions):
            idx = (self.parent.df[time_col] - pos).abs().idxmin()
            
            self.table.setItem(i, 0, QTableWidgetItem(f"Set point {i+1}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{self.parent.df[time_col].iloc[idx]:.2f} {time_unit}"))
            
            col_idx = 2
            for sig in available_signals:
                if sig in self.parent.df.columns:
                    if sig == "Dyno_Speed_[dyno_speed]":
                        value = f"{self.parent.df[sig].iloc[idx]:.1f} kph"
                    else:
                        value = f"{self.parent.df[sig].iloc[idx]:.2f}°C"
                    self.table.setItem(i, col_idx, QTableWidgetItem(value))
                    col_idx += 1
        
        self.table.resizeColumnsToContents()
        
        # Update time difference if 2 points
        if len(current_positions) == 2:
            time_diff = abs(current_positions[1] - current_positions[0])
            self.diff_label.setText(f"⏱️ Time difference: {time_diff:.2f} {time_unit}")
            self.diff_label.setFont(QFont("Arial", 12, QFont.Bold))
            self.diff_label.setAlignment(Qt.AlignCenter)
            self.diff_label.setStyleSheet("color: #0078d4; padding: 10px;")
            self.diff_label.show()
        else:
            self.diff_label.hide()
    
    def closeEvent(self, event):
        """Clean up when dialog is closed"""
        if hasattr(self.parent, 'analysis_dialog'):
            self.parent.analysis_dialog = None
        # Disconnect signal
        try:
            self.parent.setpoint_changed.disconnect(self.update_analysis)
        except:
            pass
        event.accept()


# Additional methods for ThermalAnalyzerPyQt class
ThermalAnalyzerPyQt.export_data = lambda self: self._export_data()
ThermalAnalyzerPyQt.show_summary = lambda self: self._show_summary()

def _export_data(self):
    if self.df is None:
        QMessageBox.warning(self, "Warning", "No data to export")
        return
    
    file_path, _ = QFileDialog.getSaveFileName(
        self, "Export Data", "", "CSV files (*.csv);;Excel files (*.xlsx)")
    
    if file_path:
        try:
            if file_path.endswith('.xlsx'):
                self.df.to_excel(file_path, index=False)
            else:
                self.df.to_csv(file_path, index=False)
            
            QMessageBox.information(self, "Success", f"Data exported to {os.path.basename(file_path)}")
            self.status_bar.showMessage(f"Exported to {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

def _show_summary(self):
    if self.df is None:
        QMessageBox.warning(self, "Warning", "No data loaded")
        return
    
    # Create summary window
    dialog = QWidget()
    dialog.setWindowTitle("📋 Data Summary")
    dialog.setGeometry(200, 200, 600, 700)
    dialog.setWindowModality(Qt.ApplicationModal)
    
    layout = QVBoxLayout(dialog)
    
    # Title
    title = QLabel("Thermal Data Analysis Summary")
    title.setFont(QFont("Arial", 14, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)
    
    # Summary text
    summary_text = QTextEdit()
    summary_text.setReadOnly(True)
    
    temp_cols = [c for c in self.df.columns if 'TEMP' in c]
    summary = f"""📊 THERMAL DATA ANALYSIS SUMMARY
{'='*50}

📁 Dataset Information:
• Total Records: {len(self.df):,}
• Time Range: {self.df['Elapsed_min'].min():.1f} - {self.df['Elapsed_min'].max():.1f} minutes
• Duration: {self.df['Elapsed_min'].max():.1f} minutes
• Temperature Sensors: {len(temp_cols)}

🌡️ Temperature Sensor Details:"""
    
    for col in temp_cols[:10]:
        if col in self.df.columns:
            mean_temp = self.df[col].mean()
            min_temp = self.df[col].min()
            max_temp = self.df[col].max()
            summary += f"\n• {col}:\n  - Range: {min_temp:.1f}°C to {max_temp:.1f}°C\n  - Average: {mean_temp:.1f}°C"
    
    if len(temp_cols) > 10:
        summary += f"\n... and {len(temp_cols) - 10} more sensors"
    
    summary += f"\n\n🔧 Sensor Groups:"
    if self.groups:
        for name, sensors in self.groups.items():
            if sensors and name in self.df.columns:
                mean_temp = self.df[name].mean()
                summary += f"\n• {name}: {len(sensors)} sensors (avg: {mean_temp:.1f}°C)"
    else:
        summary += "\n• No groups configured"
    
    # Speed data
    speed_col = "Dyno_Speed_[dyno_speed]"
    if speed_col in self.df.columns:
        speed_mean = self.df[speed_col].mean()
        speed_max = self.df[speed_col].max()
        summary += f"\n\n🚗 Speed Data:\n• Average Speed: {speed_mean:.1f} kph\n• Maximum Speed: {speed_max:.1f} kph"
    
    summary_text.setText(summary)
    layout.addWidget(summary_text)
    
    # Close button
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.close)
    layout.addWidget(close_btn)
    
    dialog.show()
    
    # Keep reference
    self.summary_dialog = dialog

ThermalAnalyzerPyQt._export_data = _export_data
ThermalAnalyzerPyQt._show_summary = _show_summary


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HVAC Thermal Test Analyzer")
    app.setOrganizationName("Thermal Analysis Tools")
    
    # Set application icon if available
    try:
        if os.path.exists('icon.ico'):
            app.setWindowIcon(QIcon('icon.ico'))
    except:
        pass
    
    window = ThermalAnalyzerPyQt()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
