from typing import Callable, Dict, List, Tuple, Union

from numpy.core.shape_base import block
from area_db import AreaDatabase
from data_types import BlockFloatingPoint, FixedPointWithExponent, FloatingPoint, FloatingPointVec, Data, SInt
from modules import Add, DotProduct, FloatingPointToBlockFloatingPoint, Module, Multiply
import numpy as np


class DotProductAreaHandler:
    """
    Enables estimating the area cost of the Dot products from the area costs of
    multipliers and adders.
    """

    def __init__(self, area_db: AreaDatabase) -> None:
        self._area_db = area_db

    def _area_block_floating_point(self, gen: BlockFloatingPoint, gen_accum: Data) -> float:
        n = gen.block_size
        mult_cost = self._area_db(Multiply(SInt(gen.mantissa_width)))
        add_cost = self._area_db(
            Add(SInt(gen.mantissa_width * 2) if gen_accum is None else gen_accum))
        exp_cost = self._area_db(Add(SInt(gen.exponent_width)))
        return (n - 1) * add_cost + n * mult_cost + exp_cost

    def _area_floating_point_vector(self, gen: FloatingPointVec, gen_accum: Data) -> float:
        assert(gen_accum is None and "for FloatingPointVec no different gen_accum")
        n = gen.block_size
        mult_cost = self._area_db(Multiply(gen.as_floating_point()))
        add_cost = self._area_db(
            Add(gen.as_floating_point() if gen_accum is None else gen_accum))
        return (n - 1) * add_cost + n * mult_cost

    def __call__(self, m: Module) -> Union[float, None]:
        if not isinstance(m, DotProduct):
            return None

        if isinstance(m.gen_vec, BlockFloatingPoint):
            return self._area_block_floating_point(m.gen_vec, m.gen_accum)

        if isinstance(m.gen_vec, FloatingPointVec):
            return self._area_floating_point_vector(m.gen_vec, m.gen_accum)

        return None


class FloatingPointToBlockFloatingPointAreaHandler:
    """"
    Applies linear regression by varying the block size to estimate the
    area cost of the fp2bfp component.
    """

    def __init__(
        self,
        area_db: AreaDatabase
    ) -> None:
        self._area_db = area_db
        self._estimators: Dict[Tuple[FloatingPoint,
                                     FixedPointWithExponent], Callable[[int], float]] = {}

    def add_estimator(self, gen_fp: FloatingPoint, gen_fxe: FixedPointWithExponent, block_sizes: List[int]) -> None:
        @np.vectorize
        def get_area(block_size) -> float:
            gen_bfp = BlockFloatingPoint(
                block_size, gen_fxe.exponent_width, gen_fxe.mantissa_width)
            area = self._area_db(FloatingPointToBlockFloatingPoint(gen_fp, gen_bfp))
            assert(area is not None and "not existent sample")
            return area
        # we do linear estimation
        area = get_area(block_sizes)
        z = np.polyfit(block_sizes, area, 1)
        self._estimators[(gen_fp, gen_fxe)] = np.poly1d(z)

    def __call__(self, m: Module) -> Union[float, None]:
        if not isinstance(m, FloatingPointToBlockFloatingPoint):
            return None
        
        estimator = self._estimators.get((m.gen_fp, m.gen_bfp.as_fixed_point_with_exponent()), None)
        
        if estimator is None:
            return None
        
        return estimator(m.gen_bfp.block_size)
