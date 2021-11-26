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
    area.add_on_miss(DotProductAreaHandler(area))
    
    fp2bfp_area_handler = FloatingPointToBlockFloatingPointAreaHandler(area)
    fp2bfp_area_handler.add_estimator(FloatingPoint.bfloat16, FixedPointWithExponent(10, 4), [2, 4, 6, 32])
    fp2bfp_area_handler.add_estimator(FloatingPoint.bfloat16, FixedPointWithExponent(10, 6), [2, 4, 6, 32])
    fp2bfp_area_handler.add_estimator(FloatingPoint.bfloat16, FixedPointWithExponent(10, 8), [2, 4, 6, 32])

    area.add_on_miss(fp2bfp_area_handler)

assign_handlers()


def cost_hbfp(gen_fxe: FixedPointWithExponent, gen_fp: FloatingPoint) -> Callable[[int], float]:
    @np.vectorize
    def cost(block_size: int) -> float:
        gen_bfp = BlockFloatingPoint(block_size, gen_fxe.exponent_width, gen_fxe.mantissa_width)
        gen_accum = SInt(2 * gen_fxe.mantissa_width)
        gen_fxe_output = FixedPointWithExponent(gen_fxe.exponent_width, 2 * gen_fxe.mantissa_width)
        dot_product = area(DotProduct(gen_bfp, gen_accum))
        fxe_to_fp = area(FixedPointWithExponentToFloatingPoint(gen_fxe_output, gen_fp))
        accumulator = area(Accumulator(gen_fp))
        activation = area(RELU(gen_fp))
        fp_to_bfp = area(FloatingPointToBlockFloatingPoint(gen_fp, gen_bfp))
        return dot_product + fxe_to_fp + accumulator + activation + fp_to_bfp
    return cost


def cost_fpvec(gen_fp: FloatingPoint) -> Callable[[int], float]:
    @np.vectorize
    def cost(block_size: int) -> float:
        vec_type = FloatingPointVec(block_size, gen_fp.exponent_width, gen_fp.mantissa_width)
        dot_product = area(DotProduct(vec_type))
        accumulator = area(Accumulator(gen_fp))
        activation = area(RELU(gen_fp))
        return dot_product + accumulator + activation
    return cost


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

    block_sizes = np.linspace(0, 100, 1000)
    y1 = cost_hbfp(FixedPointWithExponent(10, 8), FloatingPoint.bfloat16)(block_sizes)
    y2 = cost_hbfp(FixedPointWithExponent(10, 6), FloatingPoint.bfloat16)(block_sizes)
    y3 = cost_hbfp(FixedPointWithExponent(10, 4), FloatingPoint.bfloat16)(block_sizes)
    y0 = cost_fpvec(FloatingPoint.ieee_fp32)(block_sizes)

    plt.figure()

    plt.plot(block_sizes, y0 / y1)
    plt.plot(block_sizes, y0 / y2)
    plt.plot(block_sizes, y0 / y3)

    plt.grid()

    plt.savefig("test.png")


if __name__ == "__main__":
    main()
