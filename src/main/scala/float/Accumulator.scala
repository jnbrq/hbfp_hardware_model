package float

import chisel3._

class Accumulator(gen_fp: FloatingPoint) extends Module {
  val io = IO(new Bundle {
    val in = Input(gen_fp)
    val out = Output(gen_fp)
  })

  val acc = RegInit(gen_fp.zero)

  acc := Add(acc, io.in)(gen_fp)
  io.out := acc
}
