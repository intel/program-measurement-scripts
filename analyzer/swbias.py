from analyzer_base import PlotTab, PlotAnalyzerData
import pandas as pd
from generate_sw_bias import SWbiasPlot
from metric_names import MetricName, NonMetricName
globals().update(MetricName.__members__)

class SWbiasData(PlotAnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'SWbias', x_axis=NonMetricName.SI_SW_BIAS, y_axis=NonMetricName.SI_TIER_NORMALIZED)

class SWbiasTab(PlotTab):
    def __init__(self, parent, container):
        super().__init__(parent, container, SWbiasData, 'SWbias', [NonMetricName.SI_TIER_NORMALIZED])

    def update_plot(self):
        return super().update_plot().setData(self.analyzerData.capacityDataItems)

    def mk_plot(self):
        return SWbiasPlot()