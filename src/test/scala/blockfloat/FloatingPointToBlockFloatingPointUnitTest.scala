package blockfloat

import chisel3._
import chisel3.util._
import chisel3.iotesters._
import float._

class FloatingPointToBlockFloatingPointTop(
    val gen_floatingpoint: FloatingPoint,
    val gen_blockfloatingpoint: BlockFloatingPoint,
    val test_vec: Seq[Double]
) extends Module {
  val io = IO(new Bundle {
    val result = ValidIO(gen_blockfloatingpoint.as_fixed_point_with_exponent)
  })

  val dut = Module(
    new FloatingPointToBlockFloatingPoint(
      gen_floatingpoint,
      gen_blockfloatingpoint
    )
  )

  io.result := dut.io.out

  val values = VecInit(test_vec.map(_.to_floating_point_hw(gen_floatingpoint)))
  val idx = RegInit(0.U(32.W))

  dut.io.in.valid := idx < test_vec.length.U
  dut.io.in.bits := values(idx)
  idx := idx + 1.U
}

class FloatingPointToBlockFloatingPointTopUnitTester(
    dut: FloatingPointToBlockFloatingPointTop
) extends PeekPokeTester(dut) {
  step(dut.gen_blockfloatingpoint.block_size * 2 + 4)
}

class FloatingPointToBlockFloatingPointTester extends ChiselFlatSpec {
  "Floating point to block floating point conversion" should "work correctly" in {
    iotesters.Driver.execute(
      Array("--generate-vcd-output", "on"),
      () =>
        new FloatingPointToBlockFloatingPointTop(
          FloatingPoint.fp18,
          BlockFloatingPoint(8, 10, 8),
          Array(
            1.0,
            2.0,
            4.0,
            32.0,
            64.0,
            1.0,
            2.0,
            4.0,
          )
        )
    ) { c => new FloatingPointToBlockFloatingPointTopUnitTester(c) } should be(
      true
    )
  }
}
