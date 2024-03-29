import math
from typing import Callable, Tuple
from area_db import AreaDatabase
from modules import Add, Multiply
from data_types import FloatingPoint, SInt
import dataclasses
import os
from abc import ABC, abstractmethod
from fixed_point_estimators import register_fixed_point_estimators

DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/output"
area = AreaDatabase(DATA_DIR)

register_fixed_point_estimators(area)

# AREA_SRAM = 0.244803  # from Ahmet's paper, um^2/bit
AREA_SRAM = 1.041666  # from Mario's analysis

SAVE_FIGS = True
FIGS_PATH = "fig_output2/"


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
    
    def performance_density(s, memory_bandwidth: float) -> bool:
        """
        Returns the performance density (Throughput/Area) [TOps/mm²] of the hardware configuration.
        """
        return s.throughput() * min(1, memory_bandwidth / s.bandwidth_offchip()) / (s.area_exec_unit() / 1e6)


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
        area_sint_multiply = area(Multiply(SInt(s.len_mantissa)))
        area_sint_add = area(Add(SInt(2 * s.len_mantissa + math.ceil(math.log2(s.dim_block)) + 1)))
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
        # reuse = max(reuse, 1)

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
        # reuse = max(reuse, 1)

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

    reticle_size = 830e6
    critical_bw = 1000

    def find_good_fraction(cfg: StardustConfig):
        """
        From a given Stardust configuration, tries to find a good area percentage
        between 40% and 45% to maximize the HBM bandwidth.
        """

        @np.vectorize
        def f(fraction: int) -> float:
            cfg.maximize_onchip_area(reticle_size * fraction)
            return (cfg.bandwidth_offchip())

        x = np.arange(40.0, 46.0, 1.0)
        y = f(x)
        return math.floor(x[np.argwhere(y < critical_bw)[-1]])

    clock_frequency = 800e6

    print(f"Clock Frequency [MHz] = {clock_frequency / 1e6}")

    n = np.arange(1, 3300)

    def plot_max_bw(subplot: matplotlib.axes.Axes, x: np.ndarray) -> None:
        subplot.plot(x, x * 0.0 + critical_bw,
                     label="HBM2 Bandwidth", linestyle="--", color="#663300")

    def print_statistics(cfg: StardustConfig, area_envelope: float):
        # autopep8: off
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
        print(f"xput/area/sec   [     ] = { cfg.throughput() / cfg.clock_frequency / cfg.area_exec_unit() * 1e15 }")
        print(f"Reuse           [     ] = { cfg.reuse }")
        print(f"Perf. density   [     ] = { cfg.performance_density(critical_bw) }")
        # autopep8: on

    def plot_for(
        title: str,
        area_envelope: float,
        gen: Callable[[int], StardustConfig]
    ) -> None:
        fig = plt.figure(figsize=(4, 8))  # , dpi=300)

        bw_vs_xput = fig.add_subplot(2, 1, 1)
        bw_vs_xput.set_title(f"Memory BW vs. Throughput\nfor {title}")
        bw_vs_xput.set_ylabel("Off-chip Memory Bandwidth [GB/s]")
        bw_vs_xput.set_xlabel("Arithmetic Throughput [TOps/s]")

        pd_vs_xput = fig.add_subplot(2, 1, 2)
        pd_vs_xput.set_title(f"Perf Density vs. Throughput\nfor {title}")
        pd_vs_xput.set_ylabel("Performance Density [TOps/mm²]")
        pd_vs_xput.set_xlabel("Arithmetic Throughput [TOps/s]")

        def without_reuse() -> None:
            lim = [False, 0]
            cfgs = [None] * n.shape[0]

            @np.vectorize
            def calculate(n) -> Tuple[float, float]:
                cfg = gen(n)
                cfg.reuse = (1, 1)
                if cfg.area() > area_envelope:
                    if not lim[0]:
                        lim[0] = True
                        lim[1] = n - 1
                    return (cfg.throughput(), 0, 0)
                cfgs[n] = cfg
                return (cfg.throughput(), cfg.bandwidth_offchip(), cfg.performance_density(critical_bw))
            xput, bw, pd = calculate(n)
            plot_max_bw(bw_vs_xput, xput)

            bw_vs_xput.plot(xput[0:lim[1]], bw[0:lim[1]],
                         label="without data reuse", color="#B85450")
            bw_vs_xput.legend()

            pd_vs_xput.plot(xput[500:lim[1]], pd[500:lim[1]],
                         label="without data reuse", color="#B85450")
            pd_vs_xput.legend()

            print(">> without reuse: <<")
            print_statistics(
                cfgs[n[np.argwhere(bw[0:lim[1]] < critical_bw)[-1]][0]], area_envelope)

        def with_reuse() -> None:
            lim = [False, 0]
            cfgs = [None] * n.shape[0]

            @np.vectorize
            def calculate(n) -> Tuple[float, float]:
                cfg = gen(n)
                if not cfg.maximize_onchip_area(area_envelope):
                    if not lim[0]:
                        lim[0] = True
                        lim[1] = n - 1
                    return (cfg.throughput(), 0, 0)
                cfgs[n] = cfg
                return (cfg.throughput(), cfg.bandwidth_offchip(), cfg.performance_density(critical_bw))
            xput, bw, pd= calculate(n)

            bw_vs_xput.plot(xput[0:lim[1]], bw[0:lim[1]],
                         label="with data reuse", color="#6C8EBF")
            bw_vs_xput.legend()

            pd_vs_xput.plot(xput[500:lim[1]], pd[500:lim[1]],
                         label="with data reuse", color="#6C8EBF")
            pd_vs_xput.legend()

            print(">> with data reuse: <<")
            print_statistics(
                cfgs[n[np.argwhere(bw[0:lim[1]] < critical_bw)[-1]][0]], area_envelope)

        print(f"=== DATA FOR {title.upper()} ===")
        without_reuse()
        with_reuse()

        bw_vs_xput.set_ylim([0, 4020])
        bw_vs_xput.set_xlim([0, 6500])

        # pd_vs_xput.set_ylim([0, 10])
        # pd_vs_xput.set_xlim([0, 6500])

        if SAVE_FIGS:
            fig.tight_layout()
            fig.savefig(f"{ FIGS_PATH }/{ title }-bw.svg")
            fig.savefig(f"{ FIGS_PATH }/{ title }-bw.png")

    efficiency = 0.85  # mario's reference

    for w in [2, 3, 4, 5, 6, 8, 16, 32]:
        plot_for(
            f"hbfp{w}",
            reticle_size * efficiency,
            lambda n: StardustConfigHBFP(
                clock_frequency=clock_frequency,
                dim_array=n,
                dim_block=16,
                len_exponent=10,
                len_mantissa=w,
                floating_point=FloatingPoint.bfloat16))

    plot_for(
        "bfloat16",
        reticle_size * efficiency,
        lambda n: StardustConfigFloatingPoint(
            clock_frequency=clock_frequency,
            dim_array=n,
            floating_point=FloatingPoint.bfloat16))

    plot_for(
        "fp32",
        reticle_size * efficiency,
        lambda n: StardustConfigFloatingPoint(
            clock_frequency=clock_frequency,
            dim_array=n,
            floating_point=FloatingPoint.ieee_fp32))

    if not SAVE_FIGS:
        plt.show()


if __name__ == "__main__":
    main()
