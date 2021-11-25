package generic

import chisel3._

class Multiply[T <: Data with Num[T]](val gen: T, val gen_out: T)
    extends Module
    with BinaryOp[T] {
  val io = IO(new Bundle {
    val in_a = Input(gen)
    val in_b = Input(gen)
    val out = Output(gen_out)
  })

  io.out := io.in_a * io.in_b

  def in_a: T = io.in_a
  def in_b: T = io.in_b
  def out: T = io.out
}
