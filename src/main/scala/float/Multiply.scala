package float

import chisel3._
import chisel3.util._
import generic.BinaryOp
import generic.Delay

class Multiply(val gen_fp: FloatingPoint)
    extends Module
    with BinaryOp[FloatingPoint]
    with Delay {
  override val delay = 0

  val io = IO(new Bundle {
    val in_a = Input(gen_fp)
    val in_b = Input(gen_fp)

    val out = Output(gen_fp)
  })

  def in_a = io.in_a
  def in_b = io.in_b
  def out = io.out

  // TODO add support for subnormals, maybe
  io.out.exponent := io.in_a.exponent + io.in_b.exponent - gen_fp.exponent_offset.U

  val op_a = Cat(1.U, io.in_a.mantissa)
  val op_b = Cat(1.U, io.in_b.mantissa)
  val prod = op_a * op_b
  io.out.mantissa := prod(2 * gen_fp.mantissa_width, gen_fp.mantissa_width)
  io.out.sign := io.in_a.sign ^ io.in_b.sign
}

object Multiply {
  def apply(a: FloatingPoint, b: FloatingPoint)(implicit
      fp: FloatingPoint
  ): FloatingPoint = {
    val multiply = Module(new Multiply(fp))
    multiply.io.in_a := a
    multiply.io.in_b := b
    multiply.io.out
  }
}
