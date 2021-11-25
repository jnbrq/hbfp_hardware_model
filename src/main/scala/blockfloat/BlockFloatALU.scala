package blockfloat

import chisel3._
import chisel3.util._
import common._
import float._

class BlockFloatALU(
    val bfp: BlockFloatingPoint
) extends Module {
  val io = IO(new Bundle {
    val in = Input(new Bundle {
      val a = bfp.cloneType
      val b = bfp.cloneType
    })
    val out = Output(FloatingPoint.ieee_fp16)
  })

  val accum = RegInit(0.to_floating_point_hw(FloatingPoint.ieee_fp16))
  val products = VecInit(io.in.a.mantissas.zip(io.in.b.mantissas).map {
    case (a, b) => {
      a * b
    }
  })
  val sum = products.reduceTree(_ + _)
  val sum_fp16 = {
    val intermediate_result = sum.to_floating_point(FloatingPoint.ieee_fp16)
    val result = Wire(FloatingPoint.ieee_fp16)
    result.mantissa := intermediate_result.mantissa
    // TODO should I check for overflow here?
    result.exponent := (intermediate_result.exponent.asSInt + io.in.a.exponent + io.in.b.exponent).asUInt
    result.sign := intermediate_result.sign
    result
  }
  accum := float.Add(accum, sum_fp16, true)(FloatingPoint.ieee_fp16)
  io.out := accum
}
