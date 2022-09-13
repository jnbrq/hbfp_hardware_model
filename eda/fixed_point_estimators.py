from typing import Callable, List, Union
from area_db import AreaDatabase
from modules import Add, Module, Multiply
from data_types import Data, SInt, UInt
import os
from abc import ABC, abstractmethod
import numpy as np

class PolynomialEstimator:
    """
    A convenience class for fitting functions with polynomials.
    """

    def __init__(self, deg: int, x: List[float], y: List[float]) -> None:
        self._f = np.poly1d(np.polyfit(np.array(x), np.array(y), deg))

    def __call__(self, x: float) -> float:
        return self._f(x)


class EstimatedHandler(ABC):
    def __init__(self, estimator: Callable[[object], float]) -> None:
        self._estimator = estimator

    @abstractmethod
    def check_module(self, m: Module) -> Union[object, None]:
        """
        Checks if the area cost of the module can be estimated by this estimator.
        If it cannot be estimated, returns None, otherwise returns an object to
        be passed to the underlying estimator.
        """

    def __call__(self, m: Module) -> Union[float, None]:
        o = self.check_module(m)

        if o is None:
            return None

        return self._estimator(o)


class FixedPointEstimators(EstimatedHandler):
    def __init__(self, area_db: AreaDatabase, n: np.ndarray) -> None:
        def estimator_for(
                hwgen: Callable[[Data], Module],
                datagen: Callable[[int], Data],
                n: np.ndarray,
                deg: int) -> PolynomialEstimator:
            n = np.array(n)
            f = np.vectorize(lambda n: area_db(hwgen(datagen(n))))
            return PolynomialEstimator(deg, n, f(n))

        d = {}
        for datagen in [SInt, UInt]:
            d[(Add, datagen)] = estimator_for(Add, datagen, n, 1)
        for datagen in [SInt, UInt]:
            d[(Multiply, datagen)] = estimator_for(Multiply, datagen, n, 2)

        def estimate(m: Module):
            return d[(type(m), type(m.gen))](m.gen.width)

        super().__init__(estimator=estimate)

    def check_module(self, m: Module) -> Union[Module, None]:
        if not (isinstance(m, Multiply) or isinstance(m, Add)):
            return None

        if not (isinstance(m.gen, SInt) or isinstance(m.gen, UInt)):
            return None

        return m


def register_fixed_point_estimators(area: AreaDatabase):
    """
    Registers estimators for calculating the area of fixed-point hardware modules.
    """
    area.add_on_miss(FixedPointEstimators(area, np.arange(8, 17)))


def main() -> None:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/output"
    area = AreaDatabase(DATA_DIR)
    register_fixed_point_estimators(area)
    
    import matplotlib.pyplot as plt

    def do_plot(
            title: str,
            hwgen: Callable[[Data], object],
            n: np.ndarray,
            datagen: Callable[[int], Data] = SInt) -> None:
        n = np.array(n)
        f = np.vectorize(lambda n: area(hwgen(datagen(n))))
        fig = plt.figure()
        subplot = fig.add_subplot()
        subplot.set_title(title)
        subplot.set_xlabel("Number of Bits")
        subplot.set_ylabel("Area [μm²]")
        subplot.plot(n, f(n))

    do_plot("Multiplier Area (SInt)", Multiply, np.arange(1, 32), SInt)
    do_plot("Adder Area (SInt)", Add, np.arange(1, 32), SInt)
    plt.show()


if __name__ == "__main__":
    main()
