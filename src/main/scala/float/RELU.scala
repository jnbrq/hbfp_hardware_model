package float

import chisel3._
import generic.UnaryOp

class RELU(val gen_fp: FloatingPoint) extends Module with UnaryOp[FloatingPoint] {
  val io = IO(new Bundle {
    val in = Input(gen_fp)
    val out = Output(gen_fp)
  })

  def in = io.in
  def out = io.out

  when(io.in.sign) {
    io.out.mantissa := 0.U
    io.out.exponent := 0.U
    io.out.sign := 0.B
  }.otherwise {
    io.out <> io.in
  }
}

object RELU {
  def apply(a: FloatingPoint)(implicit fp: FloatingPoint): FloatingPoint = {
    val relu = Module(new RELU(fp))
    relu.io.in := a
    relu.io.out
  }
}
