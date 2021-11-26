package blockfloat

import chisel3._
import chisel3.util._
import float._

/**
  * This module converts a fixed point with exponent to the given
  * floating point format. It performs some shifts to make the leading
  * binary digit 1.
  *
  * @param gen_fxe
  * @param gen_fp
  */
class FixedPointWithExponentToFloatingPoint(
    val gen_fxe: FixedPointWithExponent,
    val gen_fp: FloatingPoint
) extends Module {
  val io = IO(new Bundle {
    val in = Input(gen_fxe.cloneType)
    val out = Output(gen_fp)
  })

  // TODO figure out if commenting these ones would cause any problems
  // require(gen_fp.mantissa_width + 1 >= gen_fxe.mantissa_width)
  // require(gen_fp.exponent_width >= gen_fxe.exponent_width)

  val zero = 0.0.to_floating_point_hw(gen_fp)

  private def to_floating_point_with_offset(
      x: SInt,
      offset: SInt
  ): FloatingPoint = {
    val fp = x.to_floating_point(gen_fp)
    val res = Wire(gen_fp)
    // Be on the safe side, ensure that the exponent addition is done properly
    // TODO can we do this in a better and more elegant way?
    res.exponent := Mux(
      offset > 0.S,
      fp.exponent +& offset.asUInt(),
      Mux(
        fp.exponent >= (-offset).asUInt(),
        fp.exponent -& (-offset).asUInt(),
        0.U
      )
    )
    res.sign := fp.sign
    res.mantissa := fp.mantissa
    res
  }

  io.out := to_floating_point_with_offset(io.in.mantissa, io.in.exponent)
}
