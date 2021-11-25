package blockfloat

import chisel3._
import chisel3.util._
import iotesters._
import float._
import firrtl.ir.Block

class BlockFloatALUUnitTester(dut: BlockFloatALU) extends PeekPokeTester(dut) {
  private implicit val ppt: PeekPokeTester[_] = this

  def poke_a(idx: Int, x: Int) {
    poke(dut.io.in.a.mantissas(idx), x)
  }

  def poke_b(idx: Int, x: Int) {
    poke(dut.io.in.b.mantissas(idx), x)
  }

  // poke exponents
  poke(dut.io.in.a.exponent, 1)
  poke(dut.io.in.b.exponent, -3)

  poke_a(0, 1)
  poke_b(0, 2)

  poke_a(1, 4)
  poke_b(1, 5)

  poke_a(2, 2)
  poke_b(2, 5)

  poke_a(3, 2)
  poke_b(3, 3)

  step(1)

  // Expected: 38 * w ** (sum exp)
  println(s"Result = ${ TestFloatingPoint.peek(dut.io.out).to_double.toString() }")
}

class FpFpALUTester extends ChiselFlatSpec {
  "FpFpALU" should "work correctly" in {
    iotesters.Driver.execute(
      Array("--generate-vcd-output", "on"),
      () => new BlockFloatALU(BlockFloatingPoint(4, 3, 4))
    ) { c => new BlockFloatALUUnitTester(c) } should be(true)
  }
}
