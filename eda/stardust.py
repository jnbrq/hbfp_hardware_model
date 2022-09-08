import math
from typing import Callable, Tuple
from area_db import AreaDatabase
from modules import Add, Multiply
from data_types import FloatingPoint, SInt
import dataclasses
import os
from abc import ABC, abstractmethod


DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/output"
area = AreaDatabase(DATA_DIR)

# AREA_SRAM = 0.244803  # from Ahmet's paper, um^2/bit
AREA_SRAM = 1.041666  # from Mario's analysis


def quadratic_solve(a: float, b: float, c: float) -> Tuple[float, float]:
    discr = b ** 2 - 4*a*c
    if discr < 0:
        raise ArithmeticError("No real solutions.")
    sd = math.sqrt(discr)
    return (
        (-b + sd) / (2 * a),
        (-b - sd) / (2 * a)
    )


class StardustConfig(ABC):
    clock_frequency: float
    dim_array: int
    reuse: Tuple[int, int]

    @abstractmethod
    def throughput(self) -> float:
        """
        Returns the arithmetic throughput in terms of TOps/s.
        """

    def area(self) -> float:
        """
        Returns the area in terms of um^2.
        """
        return self.area_exec_unit() + self.area_mem_onchip() + self.area_simd_unit()

    @abstractmethod
    def area_exec_unit(self) -> float:
        """
        Returns the execution unit area in terms of um^2.
        """

    @abstractmethod
    def area_simd_unit(self) -> float:
        """
        Returns the SIMD unit area in terms of um^2.
        """

    @abstractmethod
    def area_mem_onchip(self) -> float:
        """
        Returns the on-chip memory area in terms of um^2.
        """

    @abstractmethod
    def bandwidth_offchip(self) -> float:
        """
        Returns the required off-chip memory bandwidth in terms of GB/s.
        """

    @abstractmethod
    def maximize_onchip_area(s, area_envelope: float) -> bool:
        """
        Maximizes the on-chip area and reuse while staying within the area envelope.
        """


@dataclasses.dataclass(frozen=False, unsafe_hash=True)
class StardustConfigHBFP(StardustConfig):
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
        return 2 * (x + w) * (s.dim_array ** 2 * s.bfp_bits_per_elem()) + \
            (x * w) * (s.dim_array ** 2 * s.floating_point.bits())

    def throughput(s) -> float:
        return s.dim_array ** 2 * s.clock_frequency / 1e12

    def area_exec_unit(s) -> float:
        area_sint_add = area(Add(SInt(s.len_mantissa)))
        area_sint_multiply = area(Multiply(SInt(s.len_mantissa)))
        area_exp = area(Add(SInt(s.len_exponent)))
        area_float_add = area(Add(s.floating_point))
        return s.dim_array ** 2 * (area_sint_add + area_sint_multiply) + \
            (s.dim_array ** 2 / s.dim_block) * (area_float_add) + \
            (s.dim_array / s.dim_block) ** 2 * (area_exp)

    def area_simd_unit(s) -> float:
        return AREA_SRAM * 2 * (s.dim_array ** 2) * s.floating_point.bits()

    def area_mem_onchip(s) -> float:
        return AREA_SRAM * s.memsz_onchip()

    def maximize_onchip_area(s, area_envelope: float) -> bool:
        # assumptions: choose the same data reuse for both x and w
        area_envelope = area_envelope - \
            (s.area_exec_unit() + s.area_simd_unit())
        if area_envelope < 0:
            # we do not have enough space
            return False

        reuse, _ = quadratic_solve(
            s.dim_array ** 2 * s.floating_point.bits(),
            4 * s.dim_array ** 2 * s.bfp_bits_per_elem(),
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
class StardustConfigFloatingPoint(StardustConfig):
    clock_frequency: float = 800e6
    dim_array: int = 512
    floating_point: FloatingPoint = FloatingPoint.bfloat16
    reuse: Tuple[int, int] = (12, 12)

    def memsz_onchip(s) -> float:
        x, w = s.reuse
        return (2 * (x + w) + x * w) * (s.dim_array ** 2 * s.floating_point.bits())

    def throughput(s) -> float:
        return s.dim_array ** 2 * s.clock_frequency / 1e12

    def area_exec_unit(s) -> float:
        area_float_add = area(Add(s.floating_point))
        area_float_multiply = area(Multiply(s.floating_point))
        return s.dim_array ** 2 * (area_float_add + area_float_multiply)

    def area_simd_unit(s) -> float:
        return AREA_SRAM * 2 * (s.dim_array ** 2) * s.floating_point.bits()

    def area_mem_onchip(s) -> float:
        return AREA_SRAM * s.memsz_onchip()

    def maximize_onchip_area(s, area_envelope: float) -> bool:
        # assumptions: choose the same data reuse for both x and w
        area_envelope = area_envelope - \
            (s.area_exec_unit() + s.area_simd_unit())
        if area_envelope < 0:
            # we do not have enough space
            return False

        reuse, _ = quadratic_solve(
            s.dim_array ** 2 * s.floating_point.bits(),
            4 * s.dim_array ** 2 * s.floating_point.bits(),
            -area_envelope / AREA_SRAM
        )

        reuse = math.floor(reuse)

        if reuse <= 0:
            return False

        s.reuse = (reuse, reuse)
        return True

    def bandwidth_offchip(s) -> float:
        x, w = s.reuse
        return (x + w) * s.dim_array / (x * w) * s.floating_point.bits() * s.clock_frequency / (8e9)


def main() -> None:
    import numpy as np
    import matplotlib.axes
    import matplotlib.pyplot as plt

    if False:
        x = StardustConfigFloatingPoint(
            dim_array=404, floating_point=FloatingPoint.ieee_fp32)
        x.maximize_onchip_area(700e6 * 0.40)
        print(x.throughput())
        print(x.area())
        print(x.memsz_onchip() / 8e6)
        print(x.bandwidth_offchip())

    if False:
        x = StardustConfigFloatingPoint(
            dim_array=256, floating_point=FloatingPoint.ieee_fp32)
        x.maximize_onchip_area(700e6 * 0.40 * (28 / 16) ** 2)
        print(x.throughput())
        print(x.area())
        print(x.area_exec_unit() / x.area() * 100)
        print(x.memsz_onchip() / 8e6)
        print(x.bandwidth_offchip())
        return

    clock_frequency = 800e6
    # total of on-chip memory and arithmetic
    area_envelope = 700e6 * 0.40 * (28 / 16) ** 2
    critical_bw = 1000

    print(f"Area Envelope [mm²] = {area_envelope / 1e6}")
    print(f"Clock Frequency [MHz] = {clock_frequency / 1e6}")

    xlim = [0, 6100]
    ylim = [0, 4500]
    n = np.arange(1, 3300)

    def plot_max_bw(subplot: matplotlib.axes.Axes, x: np.ndarray) -> None:
        subplot.plot(x, x * 0.0 + critical_bw,
                     label="HBM2 Bandwidth", linestyle="--")

    def print_statistics(gen: Callable[[int], StardustConfig], n: int, maximize: bool):
        cfg = gen(n)
        if maximize:
            cfg.maximize_onchip_area(area_envelope)
        else:
            cfg.reuse = (1, 1)
        print(f"Clock Freq      [  MHz] = { cfg.clock_frequency }")
        print(f"Area Envelope   [  mm²] = { area_envelope / 1e6 }")
        print(f"Area            [  mm²] = { cfg.area() / 1e6 }")
        print(f"  Exec          [  mm²] = { cfg.area_exec_unit() / 1e6 }")
        print(f"  Exec          [    %] = { cfg.area_exec_unit() / cfg.area() * 100 }")
        print(f"  SIMD          [  mm²] = { cfg.area_simd_unit() / 1e6 }")
        print(f"  SIMD          [    %] = { cfg.area_simd_unit() / cfg.area() * 100 }")
        print(f"  On-Chip Mem   [  mm²] = { cfg.area_mem_onchip() / 1e6 }")
        print(f"  On-Chip Mem   [    %] = { cfg.area_mem_onchip() / cfg.area() * 100 }")
        print(f"Area / Envelope [    %] = { cfg.area() / area_envelope * 100 }")
        print(f"Array Dim       [     ] = { cfg.dim_array }")
        print(f"Off-chip BW     [ GB/s] = { cfg.bandwidth_offchip() }")
        print(f"Throughput      [TOp/s] = { cfg.throughput() }")
        print(f"xput/area/sec   [     ] = { cfg.throughput() / cfg.clock_frequency / cfg.area() * 1e15 }")
        print(f"Reuse           [     ] = { cfg.reuse }")

    def plot_for(
        title: str,
        gen: Callable[[int], StardustConfig]
    ) -> None:
        fig = plt.figure()
        subplot = fig.add_subplot()
        subplot.set_title(title)
        subplot.set_ylabel("Off-chip Memory Bandwidth [GB/s]")
        subplot.set_xlabel("Arithmetic Throughput [TOps/s]")

        def without_reuse() -> None:
            lim = [False, 0]

            @np.vectorize
            def calculate(n) -> Tuple[float, float]:
                cfg = gen(n)
                cfg.reuse = (1, 1)
                if cfg.area() > area_envelope:
                    if not lim[0]:
                        lim[0] = True
                        lim[1] = n - 1
                    return (cfg.throughput(), 0)
                return (cfg.throughput(), cfg.bandwidth_offchip())
            x, y = calculate(n)
            plot_max_bw(subplot, x)
            subplot.plot(x[0:lim[1]], y[0:lim[1]], label="without data reuse")
            subplot.legend()
            print(">> without reuse: <<")
            print_statistics(gen, n[np.argwhere(y[0:lim[1]] < critical_bw)[-1]], False)

        def with_reuse() -> None:
            lim = [False, 0]

            @np.vectorize
            def calculate(n) -> Tuple[float, float]:
                cfg = gen(n)
                if not cfg.maximize_onchip_area(area_envelope):
                    if not lim[0]:
                        lim[0] = True
                        lim[1] = n - 1
                    return (cfg.throughput(), 0)
                # print(cfg.dim_array, cfg.throughput(), cfg.area() / area_envelope * 100)
                return (cfg.throughput(), cfg.bandwidth_offchip())
            x, y = calculate(n)
            subplot.plot(x[0:lim[1]], y[0:lim[1]], label="with data reuse")
            subplot.legend()
            print(">> with data reuse: <<")
            print_statistics(gen, n[np.argwhere(y[0:lim[1]] < critical_bw)[-1]], True)

        print(f"=== DATA FOR {title.upper()} ===")
        without_reuse()
        with_reuse()

        subplot.set_ylim(ylim)
        subplot.set_xlim(xlim)

    plot_for(
        "hbfp4",
        lambda n: StardustConfigHBFP(
            clock_frequency=clock_frequency,
            dim_array=n,
            dim_block=16,
            len_exponent=10,
            len_mantissa=4,
            floating_point=FloatingPoint.bfloat16))

    plot_for(
        "bfloat16",
        lambda n: StardustConfigFloatingPoint(
            clock_frequency=clock_frequency,
            dim_array=n,
            floating_point=FloatingPoint.bfloat16))

    plot_for(
        "fp32",
        lambda n: StardustConfigFloatingPoint(
            clock_frequency=clock_frequency,
            dim_array=n,
            floating_point=FloatingPoint.ieee_fp32))

    plt.show()

    if False:
        x = StardustConfigHBFP(dim_array=2700, reuse=(1, 1))
        # x.maximize_onchip_area(700e6)
        print(x.reuse)
        print(x.area())
        x.maximize_onchip_area(700e6)
        print(x.reuse)
        print(x.area())
        return


if __name__ == "__main__":
    main()
