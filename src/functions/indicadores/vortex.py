import pandas as pd
import talib
import numpy as np

from functions.machine_learning.coletor_dados.dynamic_dataFrame_saver import (
    DynamicDataCollector,
)


class VortexIndicator:
    def __init__(self, high, low, close, period=14):
        """
        Inicializa a classe do Indicador Vortex.

        :param high: Lista ou array de preços máximos.
        :param low: Lista ou array de preços mínimos.
        :param close: Lista ou array de preços de fechamento.
        :param period: Período para o cálculo do indicador Vortex.
        """
        self.high = np.array(high, dtype=float)
        self.low = np.array(low, dtype=float)
        self.close = np.array(close, dtype=float)
        self.period = period
        self.vi_plus_data = []
        self.vi_minus_data = []

    def calculate_vortex(self):
        """
        Calcula os valores do Indicador Vortex (+VI e -VI).

        :return: Tupla com arrays dos valores +VI e -VI.
        """
        dataColetor = DynamicDataCollector(file_name="vortex_data", min_data_size=0)
        tr = talib.TRANGE(self.high, self.low, self.close)
        vmp = np.abs(self.high[1:] - self.low[:-1])
        vmm = np.abs(self.low[1:] - self.high[:-1])

        sum_tr = talib.SUM(tr, timeperiod=self.period)
        sum_vmp = talib.SUM(vmp, timeperiod=self.period)
        sum_vmm = talib.SUM(vmm, timeperiod=self.period)

        min_size = min(len(sum_vmp), len(sum_tr))
        sum_vmp = sum_vmp[:min_size]
        sum_tr = sum_tr[:min_size]

        vi_plus = sum_vmp / sum_tr
        vi_minus = sum_vmm / sum_tr
        self.vi_plus_data.extend(vi_plus)
        self.vi_minus_data.extend(vi_minus)
        data = {
            "+VI": self.vi_plus_data,
            "-VI": self.vi_minus_data,
        }
        df = pd.DataFrame(data)
        dataColetor.add_data(df)

        return df["+VI"].iloc[-1], df["-VI"].iloc[-1]
