from dataclasses import fields
from typing import Callable
from area_db import AreaDatabase
from data_types import *
from area_handlers import *
from modules import *
import numpy as np
from matplotlib import pyplot as plt
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/output"

area = AreaDatabase(DATA_DIR)


def assign_handlers():
    """
    Enables the estimation of the dot products and fp2bfp converters.
    """

    area.add_on_miss(DotProductAreaHandler(area))

    fp2bfp_area_handler = FloatingPointToBlockFloatingPointAreaHandler(area)
    fp2bfp_area_handler.add_estimator(
        FloatingPoint.bfloat16, FixedPointWithExponent(10, 4), [2, 4, 6, 32])
    fp2bfp_area_handler.add_estimator(
        FloatingPoint.bfloat16, FixedPointWithExponent(10, 5), [2, 4, 6, 32])
    fp2bfp_area_handler.add_estimator(
        FloatingPoint.bfloat16, FixedPointWithExponent(10, 6), [2, 4, 6, 32])
    fp2bfp_area_handler.add_estimator(
        FloatingPoint.bfloat16, FixedPointWithExponent(10, 7), [2, 4, 6, 32])
    fp2bfp_area_handler.add_estimator(
        FloatingPoint.bfloat16, FixedPointWithExponent(10, 8), [2, 4, 6, 32])

    area.add_on_miss(fp2bfp_area_handler)


assign_handlers()


@dataclass(frozen=True)
class HbfpAreaCost:
    dot_product: float
    fxe_to_fp: float
    accumulator: float
    activation: float
    fp_to_bfp: float

    def total(self) -> float:
        return self.dot_product + self.fxe_to_fp + self.accumulator + self.activation + self.fp_to_bfp


@dataclass(frozen=True)
class FloatingPointVecAreaCost:
    dot_product: float
    accumulator: float
    activation: float

    def total(self) -> float:
        return self.dot_product + self.accumulator + self.activation


def cost_hbfp(
        gen_fxe: FixedPointWithExponent,
        gen_fp: FloatingPoint,
        breakdown: bool = False) -> Callable[[int], float]:
    def cost(block_size: int) -> HbfpAreaCost:
        gen_bfp = BlockFloatingPoint(
            block_size, gen_fxe.exponent_width, gen_fxe.mantissa_width)
        gen_accum = SInt(2 * gen_fxe.mantissa_width)
        gen_fxe_output = FixedPointWithExponent(
            gen_fxe.exponent_width, 2 * gen_fxe.mantissa_width)
        dot_product = area(DotProduct(gen_bfp, gen_accum))
        fxe_to_fp = area(FixedPointWithExponentToFloatingPoint(
            gen_fxe_output, gen_fp))
        accumulator = area(Accumulator(gen_fp))
        activation = area(RELU(gen_fp))
        fp_to_bfp = area(FloatingPointToBlockFloatingPoint(gen_fp, gen_bfp))
        return HbfpAreaCost(dot_product, fxe_to_fp, accumulator, activation, fp_to_bfp)
    if breakdown:
        return cost
    return np.vectorize(lambda x: cost(x).total())


def cost_fpvec(gen_fp: FloatingPoint, breakdown: bool = False) -> Callable[[int], float]:
    def cost(block_size: int) -> FloatingPointVecAreaCost:
        vec_type = FloatingPointVec(
            block_size, gen_fp.exponent_width, gen_fp.mantissa_width)
        dot_product = area(DotProduct(vec_type))
        accumulator = area(Accumulator(gen_fp))
        activation = area(RELU(gen_fp))
        return FloatingPointVecAreaCost(dot_product, accumulator, activation)
    if breakdown:
        return cost
    return np.vectorize(lambda x: cost(x).total())


def main():
    if False:
        plt.figure()
        n = [2, 4, 6, 32]

        @np.vectorize
        def cost_fp2bfp(n):
            gen_fp = FloatingPoint.bfloat16
            gen_bfp = BlockFloatingPoint(n, 10, 8)
            return area(FloatingPointToBlockFloatingPoint(gen_fp, gen_bfp))
        plt.plot(n, cost_fp2bfp(n))

        gen_fp = FloatingPoint.bfloat16
        gen_bfp = BlockFloatingPoint(31, 10, 8)
        print(area(FloatingPointToBlockFloatingPoint(gen_fp, gen_bfp)))

        gen_fp = FloatingPoint.bfloat16
        gen_bfp = BlockFloatingPoint(32, 10, 8)
        print(area(FloatingPointToBlockFloatingPoint(gen_fp, gen_bfp)))

        plt.savefig("test.png")

        print(area(Add(FloatingPoint.ieee_fp32)))
        print(area(Multiply(FloatingPoint.ieee_fp32)))
        print(area(Add(UInt(10))))
        print(area(Add(SInt(16))))
        print(area(Multiply(SInt(8))))

    def compare_against_fp(gen_fp: FloatingPoint, fp_name):
        block_sizes = np.linspace(0, 50, 1000)
        fp_cost = cost_fpvec(gen_fp)(block_sizes)

        plt.figure()

        plt.title(f"{fp_name} vs. HBFP$n$ Area Comparison")
        plt.xlabel("Block Size")
        plt.ylabel("Area Ratio")

        for n in [8, 7, 6, 5, 4]:
            hbfp_cost = cost_hbfp(FixedPointWithExponent(
                10, n), FloatingPoint.bfloat16)(block_sizes)
            plt.plot(block_sizes, fp_cost / hbfp_cost,
                     label=f"{fp_name}/HBFP{n}")

        plt.grid()
        plt.legend()

        plt.savefig(f"{fp_name}_hbfp_comparison.png".lower())
        plt.savefig(f"{fp_name}_hbfp_comparison.svg".lower())

    compare_against_fp(FloatingPoint.ieee_fp32, "FP32")
    compare_against_fp(FloatingPoint.bfloat16, "bfloat16")

    def hbfp_cost():
        block_sizes = np.linspace(0, 50, 1000)

        plt.figure()

        plt.title("HBFP$n$ Area Cost")
        plt.xlabel("Block Size")
        plt.ylabel("Area Cost [$\mu m^2$]")

        for n in [8, 7, 6, 5, 4]:
            hbfp_cost = cost_hbfp(FixedPointWithExponent(
                10, n), FloatingPoint.bfloat16)(block_sizes)
            plt.plot(block_sizes, hbfp_cost, label=f"HBFP{n}")

        plt.grid()
        plt.legend()

        plt.savefig(f"hbfp_cost.png")
        plt.savefig(f"hbfp_cost.svg")

    hbfp_cost()

    def hbfp_cost_breakdown():
        mantissa_widths = [2, 3, 4, 5, 6, 7, 8]
        block_size = 32

        costs = {}

        for field in fields(HbfpAreaCost):
            costs[field.name] = []

        for mantissa_width in mantissa_widths:
            breakdown = cost_hbfp(
                FixedPointWithExponent(10, mantissa_width),
                FloatingPoint.bfloat16,
                True)(block_size)
            for field in fields(HbfpAreaCost):
                costs[field.name].append(getattr(breakdown, field.name))

        plt.figure()

        for field in fields(HbfpAreaCost):
            plt.plot(mantissa_widths,
                     costs[field.name], label=field.name, marker="o", linestyle="--")

        plt.legend()
        plt.xlabel("Mantissa Width")
        plt.ylabel("Area Cost [$\mu m^2$]")

        plt.savefig("hbfp_cost_breakdown.png")
        plt.savefig("hbfp_cost_breakdown.svg")

    hbfp_cost_breakdown()


if __name__ == "__main__":
    main()
