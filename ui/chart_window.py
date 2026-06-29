from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView

import plotly.graph_objects as go
import plotly.io as pio


class ChartWindow(QWidget):

    def __init__(self, df, x_col=None, y_col=None):
        super().__init__()

        self.setWindowTitle("Chart")
        self.resize(800, 600)

        self.df = df
        self.x_col = x_col
        self.y_col = y_col

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.web = QWebEngineView()
        layout.addWidget(self.web)

        self.render()

    def render(self):

        if self.df is None or self.df.empty:
            return

        cols = list(self.df.columns)

        x = self.x_col or cols[0]
        y = self.y_col or cols[1] if len(cols) > 1 else cols[0]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=self.df[x],
            y=self.df[y],
            mode="markers"
        ))

        html = pio.to_html(fig, full_html=False)

        self.web.setHtml(html)