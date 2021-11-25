package float

import chisel3._
import chisel3.iotesters._

class MultiplyUnitBasicTester(dut: Multiply)
    extends FloatingPointBinaryOpTester(dut, _ * _) {
  require(fp.mantissa_width >= 3)
  require(fp.exponent_width >= 3)

  override def verbose: Boolean = false

  // to keep the represented number the same, we need to offset both exponent and the mantissa
  test(
    TestFloatingPoint(false, 0 + exp_offset, 1 << (fp.mantissa_width - 3)),
    TestFloatingPoint(false, 0 + exp_offset, 4 << (fp.mantissa_width - 3))
  )
  test(
    TestFloatingPoint(false, 0 + exp_offset, 1 << (fp.mantissa_width - 3)),
    TestFloatingPoint(true, 0 + exp_offset, 4 << (fp.mantissa_width - 3))
  )
  test(
    TestFloatingPoint(false, -2 + exp_offset, 1 << (fp.mantissa_width - 3)),
    TestFloatingPoint(true, 0 + exp_offset, 4 << (fp.mantissa_width - 3))
  )
}

class MultiplyTester extends ChiselFlatSpec {
  "Multiply" should "create correct product result for basic tests." in {
    for (i <- (3 to 6)) {
      iotesters.Driver.execute(
        Array(),
        () => new Multiply(FloatingPoint(i, i))
      ) { c =>
        new MultiplyUnitBasicTester(c)
      } should be(true)
    }
  }
  
  // TODO write exhaustive tests for multiply
  /*
  "Multiply" should "create acceptable results for exhaustive tests." in {
    iotesters.Driver.execute(
      Array("", "--generate-vcd-output", "on"),
      () => new Multiply(FloatingPoint(11, 52))
    ) { c =>
      new MultiplyUnitExhaustiveTester(c)
    } should be(true)
  }
  */
}

