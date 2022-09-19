from area_db import AreaDatabase
from modules import Add, Multiply
from data_types import FloatingPoint, SInt
import os
from fixed_point_estimators import register_fixed_point_estimators

DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/output"
area = AreaDatabase(DATA_DIR)

VERBOSE = True

register_fixed_point_estimators(area)

def traditional_float_hardware(gen_fp: FloatingPoint) -> float:
    area_mul = area(Multiply(gen_fp))
    area_add = area(Add(gen_fp))
    result = area_mul + area_add
    if VERBOSE:
        print(f"traditional_float_hardware with {gen_fp=}")
        print(f"    {area_mul=}")
        print(f"    {area_add=}")
        print(f"    {result=}")
    return result

def traditional_fxpt_hardware(gen_operand: SInt, gen_accumulator: int) -> float:
    area_mul = area(Multiply(gen_operand))
    area_add = area(Add(gen_accumulator))
    result = area_mul + area_add
    if VERBOSE:
        print(f"traditional_fxpt_hardware with {gen_operand=}, {gen_accumulator=}")
        print(f"    {area_mul=}")
        print(f"    {area_add=}")
        print(f"    {result=}")
    return result

def addition_only_fixed_hardware(gen_accumulator: SInt) -> float:
    area_add = area(Add(gen_accumulator))
    coeff = 2
    result = area_add * coeff
    if VERBOSE:
        print(f"addition_only_hardware with {gen_accumulator=}")
        print(f"    {area_add=}")
        print(f"    {coeff=}")
        print(f"    {result=}")
    return result

def addition_only_float_hardware(gen_accumulator: FloatingPoint) -> float:
    area_add = area(Add(gen_accumulator))
    area_comp = area(Add(SInt(gen_accumulator.bits()))) * 1.2
    result = area_add + area_comp
    if VERBOSE:
        print(f"addition_only_float_hardware with {gen_accumulator=}")
        print(f"    {area_add=}")
        print(f"    {area_comp=}")
        print(f"    {result=}")
    return result

def main():
    traditional_float_hardware(FloatingPoint.bfloat16)
    traditional_fxpt_hardware(SInt(8), SInt(20))
    addition_only_fixed_hardware(SInt(20))
    addition_only_float_hardware(FloatingPoint.bfloat16)

if __name__ == "__main__":
    main()
