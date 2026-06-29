import pandas as pd


class DataModel:

    def __init__(self, df):
        self.df = df
        self.measures = {}

    # ---------------- REGISTER MEASURE ----------------
    def add_measure(self, name, func):

        self.measures[name] = func

    # ---------------- APPLY MEASURE ----------------
    def compute(self, measure_name, group_by=None):

        if measure_name not in self.measures:
            return None

        func = self.measures[measure_name]

        if group_by is None:
            return func(self.df)

        return self.df.groupby(group_by).apply(func)