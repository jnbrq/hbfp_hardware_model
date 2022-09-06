import math
from typing import Tuple
from area_db import AreaDatabase
from modules import Add, Multiply
from data_types import FloatingPoint, SInt
import dataclasses
import os


DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/output"
area = AreaDatabase(DATA_DIR)

AREA_SRAM = 0.244803  # from Ahmet's paper, um^2/bit


def quadratic_solve(a: float, b: float, c: float) -> Tuple[float, float]:
    discr = b ** 2 - 4*a*c
    if discr < 0:
        raise ArithmeticError("No real solutions.")
    sd = math.sqrt(discr)
    return (
        (-b + sd) / (2 * a),
        (-b - sd) / (2 * a)
    )


@dataclasses.dataclass(frozen=False, unsafe_hash=True)
class StardustConfigHBFP:
    clock_frequency: float = 800e6
    dim_array: int = 512
    dim_block: int = 16
    len_mantissa: int = 4
    len_exponent: int = 10
    floating_point: FloatingPoint = FloatingPoint.bfloat16
    reuse: Tuple[int, int] = (12, 12)

    def bfp_bits_per_elem(s) -> int:
        return (s.len_mantissa * s.dim_block ** 2 + s.len_exponent) / s.dim_block ** 2

    def memsz_onchip(s) -> float:
        x, w = s.reuse
        return (x + w) * (s.dim_array ** 2 * s.bfp_bits_per_elem()) + \
            (x * w) * (s.dim_array ** 2 * s.floating_point.bits())

    def throughput(s) -> float:
        return s.dim_array ** 2 * s.clock_frequency

    def area_exec_unit(s) -> float:
        area_sint_add = area(Add(SInt(s.len_mantissa)))
        area_sint_multiply = area(Multiply(SInt(s.len_mantissa)))
        area_exp = area(Add(SInt(s.len_exponent)))
        area_float_add = area(Add(s.floating_point))
        return s.dim_array ** 2 * (area_sint_add + area_sint_multiply) + \
            (s.dim_array ** 2 / s.dim_block) * (area_float_add) + \
                (s.dim_array / s.dim_block) ** 2 * (area_exp)

    def area_simd_unit(s) -> float:
        return AREA_SRAM * (s.dim_array ** 2) * s.floating_point.bits()

    def area_mem_onchip(s) -> float:
        return AREA_SRAM * s.memsz_onchip()

    def area(s) -> float:
        return s.area_exec_unit() + s.area_simd_unit() + s.area_mem_onchip()

    def maximize_onchip_area(s, area_envelope: float) -> bool:
        # assumptions: choose the same data reuse for both x and w
        area_envelope = area_envelope - \
            (s.area_exec_unit() + s.area_simd_unit())
        if area_envelope < 0:
            # we do not have enough space
            return False

        reuse, _ = quadratic_solve(
            s.dim_array ** 2 * s.floating_point.bits(),
            2 * s.dim_array ** 2 * s.bfp_bits_per_elem(),
            -area_envelope / AREA_SRAM
        )

        reuse = math.floor(reuse)

        if reuse <= 0:
            return False

        s.reuse = (reuse, reuse)
        return True

    def bandwidth_offchip(s) -> float:
        """
        Returns the required off-chip memory bandwidth in terms of GB/s.
        """
        x, w = s.reuse
        return (x + w) * s.dim_array / (x * w) * s.bfp_bits_per_elem() * s.clock_frequency / (8e9)


@dataclasses.dataclass(frozen=False, unsafe_hash=True)
class StardustConfigFloatingPoint:
    clock_frequency: float = 800e6
    dim_array: int = 512
    floating_point: FloatingPoint = FloatingPoint.bfloat16
    reuse: Tuple[int, int] = (12, 12)

    def memsz_onchip(s) -> float:
        x, w = s.reuse
        return (x + w + x * w) * (s.dim_array ** 2 * s.floating_point.bits())

    def throughput(s) -> float:
        return s.dim_array ** 2 * s.clock_frequency

    def area_exec_unit(s) -> float:
        area_float_add = area(Add(s.floating_point))
        area_float_multiply = area(Multiply(s.floating_point))
        return s.dim_array ** 2 * (area_float_add + area_float_multiply)

    def area_simd_unit(s) -> float:
        return AREA_SRAM * (s.dim_array ** 2) * s.floating_point.bits()

    def area_mem_onchip(s) -> float:
        return AREA_SRAM * s.memsz_onchip()

    def area(s) -> float:
        return s.area_exec_unit() + s.area_simd_unit() + s.area_mem_onchip()

    def maximize_onchip_area(s, area_envelope: float) -> bool:
        # assumptions: choose the same data reuse for both x and w
        area_envelope = area_envelope - \
            (s.area_exec_unit() + s.area_simd_unit())
        if area_envelope < 0:
            # we do not have enough space
            return False

        reuse, _ = quadratic_solve(
            s.dim_array ** 2 * s.floating_point.bits(),
            2 * s.dim_array ** 2 * s.floating_point.bits(),
            -area_envelope / AREA_SRAM
        )

        reuse = math.floor(reuse)

        if reuse <= 0:
            return False

        s.reuse = (reuse, reuse)
        return True

    def bandwidth_offchip(s) -> float:
        """
        Returns the required off-chip memory bandwidth in terms of GB/s.
        """
        x, w = s.reuse
        return (x + w) * s.dim_array / (x * w) * s.floating_point.bits() * s.clock_frequency / (8e9)

def main() -> None:
    import numpy as np
    import matplotlib.pyplot as plt

    # x = StardustConfigFloatingPoint(dim_array=641, floating_point=FloatingPoint.ieee_fp32)
    # x.maximize_onchip_area(700e6)
    # print(x.reuse)
    # return

    area_envelope = 700e6
    n = np.arange(1, 3400) # 675) # 1450) # 3400)

    plt.figure()

    def part1() -> None:
        @np.vectorize
        def calculate(n) -> Tuple[float, float]:
            cfg = StardustConfigHBFP(dim_array=n)
            # cfg = StardustConfigFloatingPoint(dim_array=n, floating_point=FloatingPoint.ieee_fp32)
            cfg.reuse = (1, 1)
            if cfg.area() > area_envelope:
                return (cfg.dim_array, 0)
                return (cfg.throughput(), 0)
            return (cfg.dim_array, cfg.bandwidth_offchip())
            return (cfg.throughput(), cfg.bandwidth_offchip())
        
        x, y = calculate(n)

        plt.plot(x, y, label="without data reuse")

    def part2() -> None:
        @np.vectorize
        def calculate(n) -> Tuple[float, float]:
            cfg = StardustConfigHBFP(dim_array=n)
            # cfg = StardustConfigFloatingPoint(dim_array=n, floating_point=FloatingPoint.ieee_fp32)
            if not cfg.maximize_onchip_area(area_envelope):
                return (cfg.dim_array, 0)
                return (cfg.throughput(), 0)
            return (cfg.dim_array, cfg.bandwidth_offchip())
            return (cfg.throughput(), cfg.bandwidth_offchip())
        
        x, y = calculate(n)

        plt.plot(x, y, label="with data reuse")

    part1()
    part2()
    plt.plot(n, n * 0.0 + 1000, label="HBM2 Bandwidth", linestyle="--")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
