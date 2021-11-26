package float

import chisel3._
import chisel3.util._
import chisel3.iotesters._

class FixedPointToFloatingPointTop(
    val signed: Boolean = true,
    val gen_fixedpoint: Bits,
    val gen_floatingpoint: FloatingPoint
) extends Module {
  val io = IO(new Bundle {
    val input = Input(gen_fixedpoint)
    val output = Output(gen_floatingpoint)
  })

  if (signed)
    io.output := io.input.asSInt().to_floating_point(gen_floatingpoint)
  else
    io.output := io.input.asUInt().to_floating_point(gen_floatingpoint)
}

class FixedPointToFloatingPointUnitTester(dut: FixedPointToFloatingPointTop)
    extends PeekPokeTester(dut) {
  implicit val fp = dut.gen_floatingpoint
  implicit val ppt: PeekPokeTester[_] = this

  def peek = TestFloatingPoint.peek(dut.io.output)

  poke(dut.io.input, 3)
  step(1)
  print(s"${peek.to_double} ${peek.toString}\n")

  poke(dut.io.input, 69)
  step(1)
  print(s"${peek.to_double} ${peek.toString}\n")

  poke(dut.io.input, 0)
  step(1)
  print(s"${peek.to_double} ${peek.toString}\n")

  poke(dut.io.input, (1 << 15) - 1)
  step(1)
  print(s"${peek.to_double} ${peek.toString}\n")

  poke(dut.io.input, -(1 << 15))
  step(1)
  print(s"${peek.to_double} ${peek.toString}\n")

  poke(dut.io.input, 0)
  step(1)
  print(s"${peek.to_double} ${peek.toString}\n")
}

class FixedPointToFloatingPointTester extends ChiselFlatSpec {
  val gen_fixedpoint_signed = SInt(16.W)
  val gen_fixedpoint_unsigned = UInt(16.W)
  val gen_floatingpoint = FloatingPoint.ieee_fp64

  "fixed-point to floating-point conversion (signed)" should "work" in {
    iotesters.Driver.execute(
      Array("--generate-vcd-output", "on"),
      () => new FixedPointToFloatingPointTop(true, gen_fixedpoint_signed, gen_floatingpoint)
    ) { c =>
      new FixedPointToFloatingPointUnitTester(c)
    } should be(true)
  }

  "fixed-point to floating-point conversion (unsigned)" should "work" in {
    iotesters.Driver.execute(
      Array("--generate-vcd-output", "on"),
      () => new FixedPointToFloatingPointTop(false, gen_fixedpoint_unsigned, gen_floatingpoint)
    ) { c =>
      new FixedPointToFloatingPointUnitTester(c)
    } should be(true)
  }
}

class FloatingPointToFixedPointTop(val gen_floatingpoint: FloatingPoint, val gen_fixedpoint: SInt)
    extends Module {
  val io = IO(new Bundle {
    val input = Input(gen_floatingpoint)
    val output = Output(gen_fixedpoint)
    val output_shifted = Output(new Bundle {
      val mantissa = SInt(8.W)
      val exponent = SInt(8.W)
    })
  })

  io.output := io.input.to_fixed_point(gen_fixedpoint)

  val shifted_floatingpoint = Wire(gen_floatingpoint)
  shifted_floatingpoint.sign := io.input.sign
  shifted_floatingpoint.mantissa := io.input.mantissa
  shifted_floatingpoint.exponent := (gen_floatingpoint.exponent_offset + 6).U
  io.output_shifted.mantissa := shifted_floatingpoint.to_fixed_point(SInt(8.W))
  io.output_shifted.exponent := io.input.exponent.asSInt - (gen_floatingpoint.exponent_offset + 8 - 2).S
}

class FloatingPointToFixedPointUnitTester(dut: FloatingPointToFixedPointTop)
    extends PeekPokeTester(dut) {
  implicit val fp = dut.gen_floatingpoint
  implicit val ppt: PeekPokeTester[_] = this

  TestFloatingPoint.from_double(0.0).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  TestFloatingPoint.from_double(-4.0).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  TestFloatingPoint.from_double(-32767).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  TestFloatingPoint.from_double(-32768).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  TestFloatingPoint.from_double(-32769).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  TestFloatingPoint.from_double(-60000).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  TestFloatingPoint.from_double(32767).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  TestFloatingPoint.from_double(32768).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  TestFloatingPoint.from_double(32769).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  TestFloatingPoint.from_double(60000).poke(dut.io.input)
  step(1)
  print(s"${peek(dut.io.output)}\n")

  def test_with_fixed_point_exponent(d: Double) = {
    TestFloatingPoint.from_double(d).poke(dut.io.input)
    step(1)
    val m = peek(dut.io.output_shifted.mantissa)
    val e = peek(dut.io.output_shifted.exponent)
    print(s"${m} ${e} ${m.toLong * math.pow(2, e.toLong)}\n")
  }

  test_with_fixed_point_exponent(2.00)
  test_with_fixed_point_exponent(2.10)
  test_with_fixed_point_exponent(2.20)
  test_with_fixed_point_exponent(2.90)
  test_with_fixed_point_exponent(0.09234)
  test_with_fixed_point_exponent(0.01004)
  test_with_fixed_point_exponent(1098)
  test_with_fixed_point_exponent(50000)
  test_with_fixed_point_exponent(0.001)
  test_with_fixed_point_exponent(0.01)
  test_with_fixed_point_exponent(0.1)
  test_with_fixed_point_exponent(1e-20)
  test_with_fixed_point_exponent(1e60)
  test_with_fixed_point_exponent(7282.875)
  test_with_fixed_point_exponent(977490935808.0)
}

class FloatingPointToFixedPointTest extends ChiselFlatSpec {
  val gen_fixedpoint = SInt(16.W)
  val gen_floatingpoint = FloatingPoint.ieee_fp32

  "floating-point to fixed-point conversion" should "work" in {
    iotesters.Driver.execute(
      Array("--generate-vcd-output", "on"),
      () => new FloatingPointToFixedPointTop(gen_floatingpoint, gen_fixedpoint)
    ) { c =>
      new FloatingPointToFixedPointUnitTester(c)
    } should be(true)
  }
}
