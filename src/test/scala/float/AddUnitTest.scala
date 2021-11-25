package float

import chisel3._
import chisel3.util._
import chisel3.iotesters._

class AddUnitBasicTester(dut: Add)
    extends FloatingPointBinaryOpTester(dut, _ + _) {
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

class AddUnitExhaustiveTester(dut: Add)
    extends FloatingPointBinaryOpTester(dut, _ + _) {
  override def verbose: Boolean = false

  val support_subnormals = false

  if (support_subnormals) {
    println("subnormals")
    test(
      TestFloatingPoint(false, 1, 0),
      TestFloatingPoint(true, 0, (1.toLong << 52) - 1)
    )
    test(TestFloatingPoint(false, 0, 1), TestFloatingPoint(true, 0, 2))
    test(TestFloatingPoint(false, 3, 1), TestFloatingPoint(false, 3, 4))
    test(TestFloatingPoint(false, 3, 1), TestFloatingPoint(true, 3, 4))
    test(TestFloatingPoint(false, 1, 1), TestFloatingPoint(true, 3, 4))
  }

  println("normals")
  // test(TestFloat(true, 2, 2095320358917637l), TestFloat(false, 2, 550504355813740l))
  test(TestFloatingPoint(false, 123, 1), TestFloatingPoint(false, 123, 4))
  test(TestFloatingPoint(false, 123, 1), TestFloatingPoint(true, 123, 4))
  test(TestFloatingPoint(false, 121, 1), TestFloatingPoint(true, 123, 4))

  println("random tests")
  for (i <- (0 until 8192)) {
    val fp1 = TestFloatingPoint.random
    val fp2 = TestFloatingPoint.random
    test(fp1, fp2)
  }

  println("random tests for same-mantissa numbers")
  for (i <- (0 until 8192)) {
    val fp1 = TestFloatingPoint.random
    val fp2 = TestFloatingPoint.random
    fp2.mantissa = fp1.mantissa
    if (!support_subnormals) {
      fp1.exponent = Math.max(fp1.exponent, 1)
      fp2.exponent = Math.max(fp2.exponent, 1)
    }
    test(fp1, fp2)
  }

  println("random tests for same-exponent numbers")
  for (i <- (0 until 8192)) {
    val fp1 = TestFloatingPoint.random
    val fp2 = TestFloatingPoint.random
    // FIXME ensure that the operation is correct even for very small
    // numbers
    fp1.exponent = math.max(fp1.exponent, 10)
    fp2.exponent = fp1.exponent
    if (!support_subnormals) {
      fp1.exponent = Math.max(fp1.exponent, 1)
      fp2.exponent = Math.max(fp2.exponent, 1)
    }
    test(fp1, fp2)
  }
}

class AddTester extends ChiselFlatSpec {
  "Add" should "create correct sum result for basic tests." in {
    for (i <- (3 to 6)) {
      iotesters.Driver.execute(
        Array(),
        () => new Add(FloatingPoint(i, i), true)
      ) { c =>
        new AddUnitBasicTester(c)
      } should be(true)

      iotesters.Driver.execute(
        Array(),
        () => new Add(FloatingPoint(i, i), false)
      ) { c =>
        new AddUnitBasicTester(c)
      } should be(true)
    }
  }

  "Add" should "create acceptable results for exhaustive tests." in {
    iotesters.Driver.execute(
      Array("", "--generate-vcd-output", "on"),
      () => new Add(FloatingPoint(11, 52), true)
    ) { c =>
      new AddUnitExhaustiveTester(c)
    } should be(true)

    iotesters.Driver.execute(
      Array("", "--generate-vcd-output", "on"),
      () => new Add(FloatingPoint(11, 52), false)
    ) { c =>
      new AddUnitExhaustiveTester(c)
    } should be(true)
  }
}
