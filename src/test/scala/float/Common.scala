package float

import chisel3._
import chisel3.iotesters._
import generic._

class FloatingPointBinaryOpTester[Dut <: Module with BinaryOp[
  FloatingPoint
] with Delay](
    dut: Dut,
    val expected_op: (Double, Double) => Double
) extends PeekPokeTester(dut) {
  implicit val ppt: PeekPokeTester[_] = this
  def verbose: Boolean = false
  implicit val fp = dut.in_a
  implicit val random = rnd
  val exp_offset = ((1 << fp.exponent_width) >> 1) - 1

  def test(
      fp1: TestFloatingPoint,
      fp2: TestFloatingPoint
  ): TestFloatingPoint = {
    fp1.poke(dut.in_a)
    fp2.poke(dut.in_b)

    step(dut.delay)

    val res = TestFloatingPoint.peek(dut.out)

    val fp1d = fp1.to_double
    val fp2d = fp2.to_double
    val resd = res.to_double
    val expected_value = expected_op(fp1d, fp2d)
    val ratio = resd / (expected_value)
    val success = ratio.isNaN() || ratio < 1.1 && ratio > 0.9
    expect(success, "Oops, not the expected ratio!")
    if (verbose || !success) {
      println(
        s"${fp1d}\t${fp2d}\t${resd}\t${expected_value}\t${fp1}\t${fp2}\t${res}\t${ratio}"
      )
    }

    res
  }
}

class FloatingPointUnaryOpTester[Dut <: Module with UnaryOp[
  FloatingPoint
] with Delay](
    dut: Dut,
    val expected_op: (Double) => Double
) extends PeekPokeTester(dut) {
  implicit val ppt: PeekPokeTester[_] = this
  def verbose: Boolean = false
  implicit val fp = dut.in
  implicit val random = rnd
  val exp_offset = ((1 << fp.exponent_width) >> 1) - 1

  def test(
      fp1: TestFloatingPoint
  ): TestFloatingPoint = {
    fp1.poke(dut.in)

    step(dut.delay)

    val res = TestFloatingPoint.peek(dut.out)

    val fp1d = fp1.to_double
    val resd = res.to_double
    val expected_value = expected_op(fp1d)
    val ratio = resd / (expected_value)
    val success = ratio.isNaN() || ratio < 1.1 && ratio > 0.9
    expect(success, "Oops, not the expected ratio!")
    if (verbose || !success) {
      println(
        s"${fp1d}\t${resd}\t${expected_value}\t${fp1}\t${res}\t${ratio}"
      )
    }

    res
  }
}
