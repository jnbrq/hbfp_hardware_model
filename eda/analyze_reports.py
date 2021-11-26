from io import *
from typing import *


def read_area_data(f: TextIOBase) -> Dict[str, Dict[str, Union[str, float]]]:
    # column names
    #  Hierarchical cell
    #  Global cell area/Absolute Total
    #  Global cell area/Percent Total
    #  Local cell area/Combinational
    #  Local cell area/Noncombinational
    #  Local cell area/Blackboxes
    #  Design

    col_count = 7

    # skip the lines
    while f.readline().strip() != "Hierarchical area distribution":
        pass
    f.readline()
    f.readline()
    f.readline()
    f.readline()
    f.readline()
    f.readline()
    f.readline()

    rows = {}

    while True:
        row: List[str] = []
        done = False
        while len(row) < col_count:
            line = f.readline()
            if line[0] == "-":
                done = True
                break
            x = line.split()
            row = row + x
        if done:
            break
        rows[row[0]] = {
            "global/absolute": float(row[1]),
            "global/percentage": float(row[2]),
            "local/combinational": float(row[3]),
            "local/noncombinational": float(row[4]),
            "local/blackboxes": float(row[5]),
            "design": row[6]
        }
    return rows


def count_leading_spaces(l: str) -> int:
    r = 0
    while r < len(l) and l[r] == " ":
        r = r + 1
    return r


def read_power_data(f: TextIOBase) -> Dict[str, Dict[str, Union[str, float]]]:
    # column names
    #  Hierarchy
    #  Switch power
    #  Int power
    #  Leak power
    #  Total power
    #  Percentage

    col_count = 6

    # skip the lines
    while True:
        line = f.readline().split()
        if len(line) > 0 and line[0] == "Hierarchy":
            break
    f.readline()

    rows = {}
    stack: List[str] = [""]
    last_level = 0

    while True:
        row: List[str] = []
        level: int = 0
        done = False
        do_count = True
        while len(row) < col_count:
            line = f.readline()
            if do_count:
                level = count_leading_spaces(line) >> 1
                do_count = False
            if line[0] == "1":
                done = True
                break
            x = line.split()
            row = row + x
        if done:
            break
        name = row[0]
        # print("last level = {} level = {}".format(last_level, level))
        if last_level >= level:
            for i in range(last_level - level + 1):
                stack.pop()
        last_level = level
        stack.append(name)
        design_name = ""
        if len(row) > col_count:
            design_name = row[1].strip("()")
            del row[1]
        rows["/".join(stack)] = {
            "switch_power": float(row[1]),
            "int_power": float(row[2]),
            "leak_power": float(row[3]),
            "total_power": float(row[4]),
            "percentage": float(row[5]),
            "design_name": design_name
        }

    return rows


def main():
    should_save_fig = True

    import numpy as np
    import matplotlib.pyplot as plt

    if True:
        mantissa = np.arange(4, 13)
        exponent = np.arange(4, 13)

        mantissa, exponent = np.meshgrid(mantissa, exponent)

        @np.vectorize
        def area(m, e):
            return read_area_data(open("RPT/floatingpoint_m{}_e{}/Add/area.log".format(m, e)))["Add"]["global/absolute"]

        z = area(mantissa, exponent)

        fig, (ax) = plt.subplots(subplot_kw={"projection": "3d"})
        ax.plot_surface(mantissa, exponent, z)
        ax.set_xlabel("Mantissa Bits")
        ax.set_ylabel("Exponent Bits")
        ax.set_zlabel("Absolute Area")
        ax.set_title("Floating Point Add Area")
        if should_save_fig:
            plt.savefig("floatingpoint_add.svg")

    if True:
        mantissa = np.arange(4, 13)
        exponent = np.arange(4, 13)

        mantissa, exponent = np.meshgrid(mantissa, exponent)

        @np.vectorize
        def area(m, e):
            return read_area_data(open("RPT/floatingpoint_m{}_e{}/Multiply/area.log".format(m, e)))["Multiply"]["global/absolute"]

        z = area(mantissa, exponent)

        fig, (ax) = plt.subplots(subplot_kw={"projection": "3d"})
        ax.plot_surface(mantissa, exponent, z)
        ax.set_xlabel("Mantissa Bits")
        ax.set_ylabel("Exponent Bits")
        ax.set_zlabel("Absolute Area")
        ax.set_title("Floating Point Multiply Area")
        if should_save_fig:
            plt.savefig("floatingpoint_multiply.svg")

    if True:
        exponent = range(4, 13)
        mantissa = np.arange(4, 13)
        fig, (ax) = plt.subplots(1, 1)
        for e in exponent:
            @np.vectorize
            def area(m):
                return read_area_data(open("RPT/floatingpoint_m{}_e{}/Add/area.log".format(m, e)))["Add"]["global/absolute"]
            z = area(mantissa)
            ax.plot(mantissa, z, label="Exp = {}".format(e))
        ax.grid()
        ax.legend()
        ax.set_xlabel("Mantissa Bits")
        ax.set_ylabel("Absolute Area")
        ax.set_title("Floating Point Add Area")
        if should_save_fig:
            plt.savefig("floatingpoint_add_2d.svg")

    if True:
        exponent = [4, 5, 7, 8, 10]
        mantissa = np.arange(4, 13)
        fig, (ax) = plt.subplots(1, 1)
        for e in exponent:
            @np.vectorize
            def area(m):
                return read_area_data(open("RPT/floatingpoint_m{}_e{}/Multiply/area.log".format(m, e)))["Multiply"]["global/absolute"]
            z = area(mantissa)
            ax.plot(mantissa, z, label="Exp = {}".format(e))
        ax.grid()
        ax.legend()
        ax.set_xlabel("Mantissa Bits")
        ax.set_ylabel("Absolute Area")
        ax.set_title("Floating Point Multiply Area")
        if should_save_fig:
            plt.savefig("floatingpoint_multiply_2d.svg")

    if True:
        width = np.arange(1, 13)
        fig, (ax) = plt.subplots(1, 1)

        @np.vectorize
        def area(w):
            return read_area_data(open("RPT/uint_w{}/Add/area.log".format(w)))["Add"]["global/absolute"]
        z = area(width)
        ax.plot(width, z)
        ax.grid()
        ax.set_xlabel("Bit Width")
        ax.set_ylabel("Absolute Area")
        ax.set_title("Unsigned Fixed Point Add Area")
        if should_save_fig:
            plt.savefig("uint_add_area.svg")

    if True:
        width = np.arange(1, 13)
        fig, (ax) = plt.subplots(1, 1)

        @np.vectorize
        def area(w):
            return read_area_data(open("RPT/uint_w{}/Multiply/area.log".format(w)))["Multiply"]["global/absolute"]
        z = area(width)
        ax.plot(width, z)
        ax.grid()
        ax.set_xlabel("Bit Width")
        ax.set_ylabel("Absolute Area")
        ax.set_title("Unsigned Fixed Point Multiply Area")
        if should_save_fig:
            plt.savefig("uint_multiply_area.svg")

    if True:
        width = np.arange(1, 13)
        fig, (ax) = plt.subplots(1, 1)

        @np.vectorize
        def area(w):
            return read_area_data(open("RPT/sint_w{}/Add/area.log".format(w)))["Add"]["global/absolute"]
        z = area(width)
        ax.plot(width, z)
        ax.grid()
        ax.set_xlabel("Bit Width")
        ax.set_ylabel("Absolute Area")
        ax.set_title("Signed Fixed Point Add Area")
        if should_save_fig:
            plt.savefig("sint_add_area.svg")

    if True:
        width = np.arange(1, 13)
        fig, (ax) = plt.subplots(1, 1)

        @np.vectorize
        def area(w):
            return read_area_data(open("RPT/sint_w{}/Multiply/area.log".format(w)))["Multiply"]["global/absolute"]
        z = area(width)
        ax.plot(width, z)
        ax.grid()
        ax.set_xlabel("Bit Width")
        ax.set_ylabel("Absolute Area")
        ax.set_title("Signed Fixed Point Multiply Area")
        if should_save_fig:
            plt.savefig("sint_multiply_area.svg")


if __name__ == "__main__":
    main()
