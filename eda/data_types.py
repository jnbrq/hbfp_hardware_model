from dataclasses import dataclass
import re
from turtle import width
from typing import Type
from common import from_string

_registered_data_types = []


class Data:
    @staticmethod
    def from_string(s: str) -> "Data":
        for t in _registered_data_types:
            try:
                return t.from_string(s)
            except:
                continue
        raise ValueError("unrecognized datatype!")


def register_dataype(t: Type) -> Type:
    _registered_data_types.append(t)
    return t


_regex_fxe = re.compile(
    r"^fxe(?P<exponent_width>[0-9]+)m(?P<mantissa_width>[0-9]+)$")
_regex_bfp = re.compile(
    r"^bfpn(?P<block_size>[0-9]+)e(?P<exponent_width>[0-9]+)m(?P<mantissa_width>[0-9]+)$")
_regex_fp = re.compile(
    r"^fpe(?P<exponent_width>[0-9]+)m(?P<mantissa_width>[0-9]+)$")
_regex_fpvec = re.compile(
    r"^fpvecn(?P<block_size>[0-9]+)e(?P<exponent_width>[0-9]+)m(?P<mantissa_width>[0-9]+)$")
_regex_uint = re.compile(r"^u(?P<width>[0-9]+)$")
_regex_sint = re.compile(r"^s(?P<width>[0-9]+)$")


@register_dataype
@from_string(_regex_fxe)
@dataclass(frozen=True)
class FixedPointWithExponent(Data):
    exponent_width: int
    mantissa_width: int

    def __repr__(self) -> str:
        return f"fxe{self.exponent_width}m{self.mantissa_width}"
    
    def bits(self) -> int:
        return self.exponent_width + self.mantissa_width


@register_dataype
@from_string(_regex_bfp)
@dataclass(frozen=True)
class BlockFloatingPoint(Data):
    block_size: int
    exponent_width: int
    mantissa_width: int

    def __repr__(self) -> str:
        return f"bfpn{self.block_size}e{self.exponent_width}m{self.mantissa_width}"

    def as_fixed_point_with_exponent(self) -> FixedPointWithExponent:
        return FixedPointWithExponent(self.exponent_width, self.mantissa_width)
    
    def bits(self) -> int:
        return self.block_size * self.mantissa_width + self.exponent_width


@register_dataype
@from_string(_regex_fp)
@dataclass(frozen=True)
class FloatingPoint(Data):
    exponent_width: int
    mantissa_width: int

    def __repr__(self) -> str:
        return f"fpe{self.exponent_width}m{self.mantissa_width}"
    
    def bits(self) -> int:
        return self.exponent_width + self.mantissa_width + 1


FloatingPoint.ieee_fp16 = FloatingPoint(5, 10)
FloatingPoint.ieee_fp32 = FloatingPoint(8, 23)
FloatingPoint.ieee_fp64 = FloatingPoint(11, 52)
FloatingPoint.fp18 = FloatingPoint(10, 7)
FloatingPoint.bfloat16 = FloatingPoint(8, 7)


@register_dataype
@from_string(_regex_fpvec)
@dataclass(frozen=True)
class FloatingPointVec(Data):
    block_size: int
    exponent_width: int
    mantissa_width: int

    def __repr__(self) -> str:
        return f"fpvecn{self.block_size}e{self.exponent_width}m{self.mantissa_width}"

    def as_floating_point(self) -> FloatingPoint:
        return FloatingPoint(self.exponent_width, self.mantissa_width)
    
    def bits(self) -> int:
        return (self.exponent_width + self.mantissa_width) * self.block_size

@register_dataype
@from_string(_regex_uint)
@dataclass(frozen=True)
class UInt(Data):
    width: int

    def __repr__(self) -> str:
        return f"u{self.width}"
    
    def bits(self) -> int:
        return width


@register_dataype
@from_string(_regex_sint)
@dataclass(frozen=True)
class SInt(Data):
    width: int

    def __repr__(self) -> str:
        return f"s{self.width}"
    
    def bits(self) -> int:
        return width
