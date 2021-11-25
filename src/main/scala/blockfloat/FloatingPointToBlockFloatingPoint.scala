package blockfloat

import chisel3._
import chisel3.util._
import float._
import common._

/**
  * This module takes a single floating point value at a time and after
  * block_size-many cycles, starts outputting the BFP tensor elements
  * one element at a time.
  *
  * @param gen_fp
  * @param gen_bfp
  */
class FloatingPointToBlockFloatingPoint(
    val gen_fp: FloatingPoint,
    val gen_bfp: BlockFloatingPoint
) extends Module {
  val io = IO(new Bundle {
    val in = Flipped(ValidIO(gen_fp))
    val out = ValidIO(gen_bfp.as_fixed_point_with_exponent)
  })

  val stored_data = Mem(gen_bfp.block_size, gen_fp)
  val max_exponent = Reg(UInt(gen_fp.exponent_width.W))
  val idx_in = Reg(UInt(12.W))
  val idx_out = Reg(UInt(12.W))

  when(!reset.asBool()) {
    idx_out := idx_out + 1.U
    when(idx_in === gen_bfp.block_size.U) {
      idx_out := 0.U
    }

    when(io.in.fire()) {
      when(idx_in === 0.U) {
        max_exponent := io.in.bits.exponent
      }.otherwise {
        max_exponent := Mux(
          max_exponent > io.in.bits.exponent,
          max_exponent,
          io.in.bits.exponent
        )
      }
      stored_data(idx_in) := io.in.bits
      idx_in := idx_in + 1.U
    }.otherwise {
      idx_in := 0.U
    }
  }
  io.out.valid := ShiftRegister(
    io.in.valid && !reset.asBool(),
    gen_bfp.block_size + 1
  )

  io.out.bits.exponent := ChiselUtils.uint_diff(
    max_exponent,
    (gen_fp.exponent_offset + gen_bfp.mantissa_width - 2).U
  )

  val elem = stored_data(idx_out)

  io.out.bits.mantissa := {
    {
      val shifted = Wire(gen_fp)
      shifted.sign := elem.sign
      shifted.mantissa := elem.mantissa
      shifted.exponent := Mux(
        elem.exponent === 0.U,
        0.U,
        ChiselUtils.uint_diff_saturate(
          elem.exponent +& gen_fp.exponent_offset.U +& gen_bfp.mantissa_width.U,
          2.U +& max_exponent
        )
      )
      shifted.to_fixed_point(SInt(gen_bfp.mantissa_width.W))
    }
  }

  dontTouch(io.in.bits.mantissa)
}
