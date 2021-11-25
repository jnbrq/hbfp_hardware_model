package generic

import chisel3._

class Add[T <: Data with Num[T]](val gen: T)
    extends Module
    with BinaryOp[T] {
  val io = IO(new Bundle {
    val in_a = Input(gen)
    val in_b = Input(gen)
    val out = Output(gen)
  })

  io.out := io.in_a + io.in_b

  def in_a: T = io.in_a
  def in_b: T = io.in_b
  def out: T = io.out
}
