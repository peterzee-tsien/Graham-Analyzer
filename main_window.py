import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFrame, QGridLayout, QGroupBox,
    QProgressBar, QMessageBox, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from data_fetcher import DataFetcher
from graham_valuation import GrahamValuation

class WorkerThread(QThread):
    finished = pyqtSignal(dict, dict, object)
    error = pyqtSignal(str)

    def __init__(self, ticker, period="1y"):
        super().__init__()
        self.ticker = ticker
        self.period = period

    def run(self):
        data, err = DataFetcher.get_stock_data(self.ticker, self.period)
        if err:
            self.error.emit(err)
        else:
            valuation = GrahamValuation.evaluate(data)
            self.finished.emit(data, valuation, data['history'])


class ChartWorkerThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, ticker, period):
        super().__init__()
        self.ticker = ticker
        self.period = period

    def run(self):
        history = DataFetcher.get_history(self.ticker, self.period)
        if history.empty:
            self.error.emit("Failed to fetch historical data for this period.")
        else:
            self.finished.emit(history)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Benjamin Graham Stock Valuation")
        self.resize(1100, 750)
        self.worker = None
        self.chart_worker = None
        self.current_ticker = None
        self.current_period = "1y"
        self.current_valuation = None

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Set Wealthsimple-style Light Theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #FFFFFF;
                color: #1A1A1A;
                font-family: "Inter", -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Segoe UI", sans-serif;
            }
            QLineEdit {
                background-color: #F5F5F5;
                border: 1px solid #EAEAEA;
                border-radius: 20px;
                padding: 12px 20px;
                font-size: 16px;
                color: #1A1A1A;
            }
            QLineEdit:focus {
                border: 1px solid #1A1A1A;
                background-color: #FFFFFF;
            }
            QPushButton {
                background-color: #1A1A1A;
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QPushButton:checked {
                background-color: #E2E8F0;
                color: #1A1A1A;
            }
            QPushButton:disabled {
                background-color: #EAEAEA;
                color: #A0A0A0;
            }
            QGroupBox {
                border: 1px solid #EAEAEA;
                border-radius: 16px;
                margin-top: 1.5ex;
                padding-top: 15px;
                font-weight: 600;
                font-size: 15px;
                color: #555555;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 15px;
                top: 5px;
            }
            QLabel {
                font-size: 15px;
                color: #1A1A1A;
            }
            QTabWidget::pane {
                border: 1px solid #EAEAEA;
                border-radius: 16px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F5F5F5;
                color: #555555;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                padding: 12px 24px;
                margin-right: 4px;
                font-weight: 600;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #1A1A1A;
                border-top: 1px solid #EAEAEA;
                border-left: 1px solid #EAEAEA;
                border-right: 1px solid #EAEAEA;
                border-bottom: 2px solid #1A1A1A;
            }
            QProgressBar {
                border: none;
                background-color: #F5F5F5;
                height: 4px;
            }
            QProgressBar::chunk {
                background-color: #1A1A1A;
            }
        """)

        # ------------------- Top Bar -------------------
        top_bar = QHBoxLayout()
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("Enter Stock Ticker (e.g. AAPL, BRK-B)")
        self.ticker_input.returnPressed.connect(self.search_stock)
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_stock)

        top_bar.addWidget(self.ticker_input)
        top_bar.addWidget(self.search_btn)
        
        # ------------------- Content Area -------------------
        content_layout = QHBoxLayout()
        
        # Left Panel (Fundamentals)
        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(350)
        left_vbox = QVBoxLayout(self.left_panel)
        
        # Basic Info Group
        info_group = QGroupBox("Basic Information")
        self.info_layout = QGridLayout()
        info_group.setLayout(self.info_layout)
        
        self.lbl_name = QLabel("Name: N/A")
        self.lbl_price = QLabel("Current Price: $0.00")
        self.lbl_pe = QLabel("P/E Ratio: 0.0")
        self.lbl_pb = QLabel("P/B Ratio: 0.0")
        self.lbl_eps = QLabel("EPS (TTM): $0.00")
        self.lbl_bvps = QLabel("BVPS: $0.00")
        
        self.info_layout.addWidget(self.lbl_name, 0, 0, 1, 2)
        self.info_layout.addWidget(self.lbl_price, 1, 0)
        self.info_layout.addWidget(self.lbl_pe, 2, 0)
        self.info_layout.addWidget(self.lbl_pb, 2, 1)
        self.info_layout.addWidget(self.lbl_eps, 3, 0)
        self.info_layout.addWidget(self.lbl_bvps, 3, 1)

        # Graham Valuation Group
        graham_val_group = QGroupBox("Graham Valuation (Deep Value)")
        self.graham_val_layout = QVBoxLayout()
        graham_val_group.setLayout(self.graham_val_layout)
        
        self.lbl_graham_num = QLabel("Graham Number: $0.00")
        font = self.lbl_graham_num.font()
        font.setBold(True)
        self.lbl_graham_num.setFont(font)
        
        self.lbl_margin = QLabel("Graham Margin: 0.0%")
        
        self.graham_val_layout.addWidget(self.lbl_graham_num)
        self.graham_val_layout.addWidget(self.lbl_margin)

        # Intrinsic Valuation Group
        intrinsic_val_group = QGroupBox("Intrinsic Valuation (Growth)")
        self.intrinsic_val_layout = QVBoxLayout()
        intrinsic_val_group.setLayout(self.intrinsic_val_layout)
        
        self.lbl_intrinsic_val = QLabel("Intrinsic Value: $0.00")
        self.lbl_intrinsic_val.setFont(font)
        
        self.lbl_intrinsic_margin = QLabel("Intrinsic Margin: 0.0%")
        
        self.intrinsic_val_layout.addWidget(self.lbl_intrinsic_val)
        self.intrinsic_val_layout.addWidget(self.lbl_intrinsic_margin)
        
        # Criteria Group
        crit_group = QGroupBox("Checklist")
        self.crit_layout = QVBoxLayout()
        crit_group.setLayout(self.crit_layout)
        self.lbl_def_score = QLabel("Defensive Score: 0/6")
        self.lbl_ent_score = QLabel("Enterprising Score: 0/5")
        self.crit_layout.addWidget(self.lbl_def_score)
        self.crit_layout.addWidget(self.lbl_ent_score)

        left_vbox.addWidget(info_group)
        left_vbox.addWidget(graham_val_group)
        left_vbox.addWidget(intrinsic_val_group)
        left_vbox.addWidget(crit_group)
        left_vbox.addStretch()

        # Right Panel (Chart)
        self.right_panel = QWidget()
        right_vbox = QVBoxLayout(self.right_panel)
        
        # Timeframe Tabs/Buttons
        self.timeframe_layout = QHBoxLayout()
        self.timeframe_group = QButtonGroup(self)
        self.timeframe_group.setExclusive(True)
        
        timeframes = [("1D", "1d"), ("1W", "5d"), ("1M", "1mo"), 
                      ("3M", "3mo"), ("1Y", "1y"), ("5Y", "5y"), ("MAX", "max")]
        
        for label, period in timeframes:
            btn = QPushButton(label)
            btn.setCheckable(True)
            if period == "1y":
                btn.setChecked(True)
            self.timeframe_group.addButton(btn)
            self.timeframe_layout.addWidget(btn)
            btn.clicked.connect(lambda checked, p=period: self.change_timeframe(p))
            
        right_vbox.addLayout(self.timeframe_layout)
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        right_vbox.addWidget(self.canvas)
        
        # Setup annotation for hover
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.5", fc="#FFFFFF", ec="#1A1A1A", lw=1, alpha=0.9),
                    arrowprops=dict(arrowstyle="->", color="#1A1A1A"),
                    color="#1A1A1A", fontweight="bold", fontsize=10)
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.hover)
        
        content_layout.addWidget(self.left_panel)
        content_layout.addWidget(self.right_panel)

        # ------------------- Recommendations Area -------------------
        from PyQt6.QtWidgets import QTabWidget
        self.rec_tabs = QTabWidget()
        
        # Graham Tab
        self.graham_tab = QWidget()
        graham_layout = QVBoxLayout(self.graham_tab)
        self.lbl_graham_rec = QLabel("GRAHAM REC: READY")
        self.lbl_graham_rec.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_font = QFont("Arial", 16, QFont.Weight.Bold)
        self.lbl_graham_rec.setFont(banner_font)
        self.lbl_graham_rec.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.lbl_graham_rec.setStyleSheet("background-color: lightgray;")
        graham_layout.addWidget(self.lbl_graham_rec)
        self.rec_tabs.addTab(self.graham_tab, "Graham Method (Deep Value)")
        
        # Intrinsic Tab
        self.intrinsic_tab = QWidget()
        intrinsic_layout = QVBoxLayout(self.intrinsic_tab)
        self.lbl_intrinsic_rec = QLabel("INTRINSIC REC: READY")
        self.lbl_intrinsic_rec.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_intrinsic_rec.setFont(banner_font)
        self.lbl_intrinsic_rec.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.lbl_intrinsic_rec.setStyleSheet("background-color: lightgray;")
        intrinsic_layout.addWidget(self.lbl_intrinsic_rec)
        self.rec_tabs.addTab(self.intrinsic_tab, "Intrinsic Value (Growth)")
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)
        self.progress.hide()

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.progress)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.rec_tabs)

    def search_stock(self):
        ticker = self.ticker_input.text().strip().upper()
        if not ticker:
            return

        self.current_ticker = ticker
        self.search_btn.setEnabled(False)
        self.progress.show()
        
        self.lbl_graham_rec.setText("FETCHING DATA...")
        self.lbl_graham_rec.setStyleSheet("background-color: lightblue;")
        self.lbl_intrinsic_rec.setText("FETCHING DATA...")
        self.lbl_intrinsic_rec.setStyleSheet("background-color: lightblue;")

        self.worker = WorkerThread(ticker, self.current_period)
        self.worker.finished.connect(self.on_data_fetched)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def change_timeframe(self, period):
        if self.current_period == period:
            return
        
        self.current_period = period
        
        if not self.current_ticker:
            return
            
        # Disable buttons temporarily
        for btn in self.timeframe_group.buttons():
            btn.setEnabled(False)
            
        self.progress.show()
        
        self.chart_worker = ChartWorkerThread(self.current_ticker, period)
        self.chart_worker.finished.connect(self.on_chart_fetched)
        self.chart_worker.error.connect(self.on_chart_error)
        self.chart_worker.start()
        
    def on_chart_error(self, err_msg):
        self.progress.hide()
        for btn in self.timeframe_group.buttons():
            btn.setEnabled(True)
        QMessageBox.warning(self, "Chart Error", err_msg)

    def on_chart_fetched(self, history):
        self.progress.hide()
        for btn in self.timeframe_group.buttons():
            btn.setEnabled(True)
        self.update_chart(history)

    def on_error(self, err_msg):
        self.search_btn.setEnabled(True)
        self.progress.hide()
        self.lbl_graham_rec.setText("ERROR")
        self.lbl_graham_rec.setStyleSheet("background-color: red; color: white;")
        self.lbl_intrinsic_rec.setText("ERROR")
        self.lbl_intrinsic_rec.setStyleSheet("background-color: red; color: white;")
        QMessageBox.critical(self, "Error", err_msg)

    def on_data_fetched(self, data, valuation, history):
        self.search_btn.setEnabled(True)
        self.progress.hide()
        
        self.current_valuation = valuation

        info = data["basic_info"]
        fund = data["fundamentals"]

        # Update Basic Info
        self.lbl_name.setText(f"Name: {info.get('name')}")
        self.lbl_price.setText(f"Current Price: ${info.get('current_price'):.2f}")
        self.lbl_pe.setText(f"P/E Ratio: {info.get('pe_ratio'):.2f}")
        self.lbl_pb.setText(f"P/B Ratio: {info.get('pb_ratio'):.2f}")
        self.lbl_eps.setText(f"EPS (TTM): ${fund.get('eps_ttm'):.2f}")
        self.lbl_bvps.setText(f"BVPS: ${fund.get('book_value_per_share'):.2f}")

        # Update Valuation
        self.lbl_graham_num.setText(f"Graham Number: ${valuation['graham_number']:,.2f}")
        self.lbl_margin.setText(f"Graham Margin: {valuation['margin_of_safety']*100:.1f}%")
        self.lbl_intrinsic_val.setText(f"Intrinsic Value: ${valuation['intrinsic_value']:,.2f}")
        self.lbl_intrinsic_margin.setText(f"Intrinsic Margin: {valuation['intrinsic_margin']*100:.1f}%")

        self.lbl_def_score.setText(f"Defensive Score: {valuation['defensive_score']}/{len(valuation['defensive_criteria'])}")
        self.lbl_ent_score.setText(f"Enterprising Score: {valuation['enterprising_score']}/{len(valuation['enterprising_criteria'])}")

        # Update Recommendation Banner
        graham_rec = valuation.get("graham_recommendation", "N/A")
        intrinsic_rec = valuation.get("intrinsic_recommendation", "N/A")
        
        self.lbl_graham_rec.setText(f"GRAHAM REC: {graham_rec}")
        self.lbl_intrinsic_rec.setText(f"INTRINSIC REC: {intrinsic_rec}")
        
        def apply_rec_style(label, rec):
            if rec == "BUY":
                label.setStyleSheet("background-color: #a8df65; color: black;") # Green
            elif rec == "HOLD":
                label.setStyleSheet("background-color: #ffd271; color: black;") # Yellow
            else:
                label.setStyleSheet("background-color: #ef4f4f; color: white;") # Red
                
        apply_rec_style(self.lbl_graham_rec, graham_rec)
        apply_rec_style(self.lbl_intrinsic_rec, intrinsic_rec)

        self.update_chart(history)

    def update_chart(self, history):
        self.current_history = history
        self.ax.clear()
        if not history.empty:
            self.ax.plot(history.index, history['Close'], label='Price', color='#1A1A1A', linewidth=1.5)
            
            # Re-add annotation because clear() removes it
            self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.5", fc="#FFFFFF", ec="#1A1A1A", lw=1, alpha=0.9),
                        arrowprops=dict(arrowstyle="->", color="#1A1A1A"),
                        color="#1A1A1A", fontweight="bold", fontsize=10)
            self.annot.set_visible(False)
            
            if self.current_valuation and self.current_valuation['graham_number'] > 0:
                self.ax.axhline(y=self.current_valuation['graham_number'], color='g', linestyle='--', label='Graham Number')
                
            if self.current_valuation and self.current_valuation.get('intrinsic_value', 0) > 0:
                self.ax.axhline(y=self.current_valuation['intrinsic_value'], color='purple', linestyle=':', label='Intrinsic Value')
            
            period_labels = {"1d": "1 Day", "5d": "1 Week", "1mo": "1 Month", 
                             "3mo": "3 Months", "1y": "1 Year", "5y": "5 Years", "max": "MAX"}
            title_period = period_labels.get(self.current_period, self.current_period)
            
            ticker_name = self.current_ticker if self.current_ticker else self.ticker_input.text().upper()
            self.ax.set_title(f"{ticker_name} - {title_period} History")
            self.ax.set_ylabel("Price (USD)")
            self.ax.grid(True)
            self.ax.legend()
            
            # Format X-axis based on timeframe
            if self.current_period in ['1d', '5d']:
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            elif self.current_period in ['1mo', '3mo']:
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            elif self.current_period == '1y':
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                self.ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            else: # 5y or max
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                self.ax.xaxis.set_major_locator(mdates.YearLocator())
                
            self.figure.autofmt_xdate()
            
        self.canvas.draw()

    def hover(self, event):
        if event.inaxes == self.ax:
            if not hasattr(self, 'current_history') or self.current_history is None or self.current_history.empty:
                return
            
            x_mouse = event.xdata
            y_mouse = event.ydata
            if x_mouse is None or y_mouse is None:
                return

            # Convert index to numeric for distance calculation
            x_data = mdates.date2num(self.current_history.index)
            y_data = self.current_history['Close'].values
            
            # Find closest x-coordinate data point
            idx = (np.abs(x_data - x_mouse)).argmin()
            x_closest = x_data[idx]
            y_closest = y_data[idx]
            
            self.annot.xy = (x_closest, y_closest)
            
            # Format tooltip date based on timeframe
            if self.current_period in ['1d', '5d']:
                dt_str = self.current_history.index[idx].strftime('%b %d, %H:%M')
            elif self.current_period in ['1mo', '3mo', '1y']:
                dt_str = self.current_history.index[idx].strftime('%b %d, %Y')
            else:
                dt_str = self.current_history.index[idx].strftime('%b %Y')
                
            self.annot.set_text(f"{dt_str}\n${y_closest:.2f}")
            
            # Adjust alignment to keep it on screen
            xlim = self.ax.get_xlim()
            if x_closest > (xlim[0] + xlim[1]) / 2:
                self.annot.xyann = (-10, 20)
                self.annot.set_horizontalalignment('right')
            else:
                self.annot.xyann = (10, 20)
                self.annot.set_horizontalalignment('left')

            self.annot.set_visible(True)
            self.canvas.draw_idle()
        else:
            if hasattr(self, 'annot') and self.annot.get_visible():
                self.annot.set_visible(False)
                self.canvas.draw_idle()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
