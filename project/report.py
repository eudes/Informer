class Report:
    # TODO: usarla siempre que se use un report (para viejos informes, por ejemplo)

    def __init__(self, report=None, formatted_report=""):
        if report is None: report = []
        self.report = report
        self.formatted_report = formatted_report

    def __repr__(self):
        return str(self.__dict__)
