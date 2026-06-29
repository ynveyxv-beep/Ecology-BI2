import plotly.express as px

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget


class PlotWidget(QWidget):

    def __init__(self, chart_type="scatter", df=None, x_col=None, y_col=None):
        super().__init__()

        self.chart_type = chart_type
        self.df = df
        self.x_col = x_col
        self.y_col = y_col

        self.setMinimumSize(300, 200)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)

        self.render_plot()

    def set_data(self, df, x_col=None, y_col=None):
        self.df = df
        self.x_col = x_col
        self.y_col = y_col
        self.render_plot()

    def render_plot(self):

        if self.df is None:
            df = px.data.iris()

            if self.chart_type == "scatter":
                fig = px.scatter(df, x="sepal_width", y="sepal_length")

            elif self.chart_type == "bar":
                fig = px.bar(df, x="species", y="sepal_width")

            else:
                fig = px.pie(df, names="species")

        else:

            df = self.df
            cols = list(df.columns)

            x = self.x_col or cols[0]
            y = self.y_col or cols[1]

            if self.chart_type == "scatter":
                fig = px.scatter(df, x=x, y=y)

            elif self.chart_type == "bar":
                fig = px.bar(df, x=x, y=y)

            else:
                fig = px.pie(df, names=x)

        html = fig.to_html(include_plotlyjs="cdn", full_html=False)

        html = html.replace(
            "</head>",
            """
            <style>
                html, body {
                    margin:0;
                    padding:0;
                    width:100%;
                    height:100%;
                    overflow:hidden;
                }
            </style>
            </head>
            """
        )

        self.browser.setHtml(html, QUrl("about:blank"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_plot()