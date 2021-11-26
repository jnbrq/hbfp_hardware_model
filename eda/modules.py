from dataclasses import dataclass
import re
from typing import Type
from data_types import *
from common import from_string

_regex_mult = re.compile(r"^op_(?P<gen>[^_]+)_mult$")
_regex_add = re.compile(r"^op_(?P<gen>[^_]+)_add$")
_regex_act = re.compile(r"^op_(?P<gen>[^_]+)_act$")
_regex_dot = re.compile(r"^op_(?P<gen>[^_]+)_dot$")
_regex_fxe2fp = re.compile(r"^fxe2fp_(?P<gen_fxe>[^_]+)_(?P<gen_fp>[^_]+)$")
_regex_fp2bfp = re.compile(r"^fp2bfp_(?P<gen_fp>[^_]+)_(?P<gen_bfp>[^_]+)$")
_regex_accum = re.compile(r"^accum_(?P<gen_fp>[^_]+)$")

_registered_modules = []


class Module:
    @staticmethod
    def from_string(s: str) -> "Module":
        for t in _registered_modules:
            try:
                return t.from_string(s)
            except:
                continue
        raise ValueError("unrecognized module!")


def register_module(t: Type) -> Type:
    _registered_modules.append(t)
    return t


@register_module
@from_string(_regex_mult)
@dataclass(frozen=True)
class Multiply(Module):
    gen: Data


@register_module
@from_string(_regex_add)
@dataclass(frozen=True)
class Add(Module):
    gen: Data


@register_module
@from_string(_regex_act)
@dataclass(frozen=True)
class RELU(Module):
    gen: Data


@register_module
@from_string(_regex_dot)
@dataclass(frozen=True)
class DotProduct(Module):
    gen_vec: Data
    gen_accum: Data = None


@register_module
@from_string(_regex_fxe2fp)
@dataclass(frozen=True)
class FixedPointWithExponentToFloatingPoint(Module):
    gen_fxe: FixedPointWithExponent
    gen_fp: FloatingPoint


@register_module
@from_string(_regex_fp2bfp)
@dataclass(frozen=True)
class FloatingPointToBlockFloatingPoint(Module):
    gen_fp: FloatingPoint
    gen_bfp: BlockFloatingPoint


@register_module
@from_string(_regex_accum)
@dataclass(frozen=True)
class Accumulator(Module):
    gen_fp: FloatingPoint
