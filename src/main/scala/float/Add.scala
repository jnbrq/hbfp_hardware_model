package float

import chisel3._
import chisel3.util._
import generic.BinaryOp
import generic.Delay

class Add(val gen_fp: FloatingPoint, val combinational: Boolean = false)
    extends Module
    with BinaryOp[FloatingPoint]
    with Delay {
  override val delay = if (combinational) 0 else 4

  val io = IO(new Bundle {
    val in_a = Input(gen_fp)
    val in_b = Input(gen_fp)

    val out = Output(gen_fp)
  })

  def in_a = io.in_a
  def in_b = io.in_b
  def out = io.out

  if (!combinational) {
    // We have a 5 stage pipeline (a delay of 4)
    val r0_s = Reg(gen_fp) // smaller
    val r0_b = Reg(gen_fp) // bigger

    val r1_result_mantissa = Reg(UInt((gen_fp.mantissa_width + 2).W))
    val r1_b = Reg(gen_fp)

    val r2_shift = Reg(UInt(chisel3.util.log2Ceil(gen_fp.mantissa_width + 2).W))
    val r2_result_mantissa = Reg(UInt((gen_fp.mantissa_width + 2).W))
    val r2_b = Reg(gen_fp)

    val r3_output = Reg(gen_fp)

    r1_b := r0_b
    r2_b := r1_b

    r2_result_mantissa := r1_result_mantissa

    io.out := r3_output

    // stage 0

    // find the smaller and the bigger one
    when(io.in_a.exponent > io.in_b.exponent) {
      r0_b := io.in_a
      r0_s := io.in_b
    }.elsewhen(io.in_a.exponent < io.in_b.exponent) {
      r0_b := io.in_b
      r0_s := io.in_a
    }.otherwise {
      when(io.in_a.mantissa > io.in_b.mantissa) {
        r0_b := io.in_a
        r0_s := io.in_b
      }.otherwise {
        r0_b := io.in_b
        r0_s := io.in_a
      }
    }

    // stage 1

    // expand the numbers with initial 1s or 0s
    val exp_diff = (r0_b.exponent -% r0_s.exponent)
    val s_mantissa_extended =
      Mux(
        exp_diff >= gen_fp.mantissa_width.U,
        0.U,
        Cat(r0_s.exponent =/= 0.U, r0_s.mantissa) >> exp_diff
      )
    val b_mantissa_extended = Cat(r0_b.exponent =/= 0.U, r0_b.mantissa)

    val sum = b_mantissa_extended +& s_mantissa_extended
    val diff = b_mantissa_extended -& s_mantissa_extended

    val same_signed = r0_s.sign === r0_b.sign
    r1_result_mantissa := Mux(same_signed, sum, diff)

    // stage 2

    // Normalize
    r2_shift := PriorityEncoder(Reverse(r1_result_mantissa))

    // stage 3

    val result_mantissa_shifted_normal = (r2_result_mantissa << r2_shift) >> 1
    val result_mantissa_shifted_subnormal =
      (r2_result_mantissa << (r2_b.exponent(r2_shift.getWidth - 1, 0))) >> 1

    when(r2_result_mantissa === 0.U) {
      r3_output.mantissa := 0.U
      r3_output.exponent := 0.U
      r3_output.sign := 0.B
    }.otherwise {
      when(r2_shift > r2_b.exponent + 1.U) {
        // subnormal
        // notice that in case b.exponent = 0, b.exponent - 1 yields the wrong result
        // that's why we do first << then >>
        r3_output.mantissa := result_mantissa_shifted_subnormal(
          gen_fp.mantissa_width - 1,
          0
        )
        r3_output.exponent := 0.U
        r3_output.sign := r2_b.sign
      }.otherwise {
        // normal
        r3_output.mantissa := result_mantissa_shifted_normal(
          gen_fp.mantissa_width - 1,
          0
        )
        r3_output.exponent := r2_b.exponent - r2_shift + 1.U
        r3_output.sign := r2_b.sign
      }
    }
  } else {
    // smaller
    val s = Wire(gen_fp)

    // bigger
    val b = Wire(gen_fp)

    // find the smaller and the bigger one
    when(io.in_a.exponent > io.in_b.exponent) {
      b := io.in_a
      s := io.in_b
    }.elsewhen(io.in_a.exponent < io.in_b.exponent) {
      b := io.in_b
      s := io.in_a
    }.otherwise {
      when(io.in_a.mantissa > io.in_b.mantissa) {
        b := io.in_a
        s := io.in_b
      }.otherwise {
        b := io.in_b
        s := io.in_a
      }
    }

    // expand the numbers with initial 1s or 0s
    val exp_diff = (b.exponent -% s.exponent)
    val s_mantissa_extended = Mux(
      exp_diff >= gen_fp.mantissa_width.U,
      0.U,
      Cat(s.exponent =/= 0.U, s.mantissa) >> exp_diff
    )
    val b_mantissa_extended = Cat(b.exponent =/= 0.U, b.mantissa)

    val sum = b_mantissa_extended +& s_mantissa_extended
    val diff = b_mantissa_extended -& s_mantissa_extended

    val same_signed = s.sign === b.sign
    val result_mantissa = Mux(same_signed, sum, diff)

    // Normalize
    val shift = PriorityEncoder(Reverse(result_mantissa))

    val result_mantissa_shifted_normal = (result_mantissa << shift) >> 1
    val result_mantissa_shifted_subnormal =
      (result_mantissa << (b.exponent(shift.getWidth - 1, 0))) >> 1

    when(result_mantissa === 0.U) {
      io.out.mantissa := 0.U
      io.out.exponent := 0.U
      io.out.sign := 0.B
    }.otherwise {
      when(shift > b.exponent + 1.U) {
        // subnormal
        // notice that in case b.exponent = 0, b.exponent - 1 yields the wrong result
        // that's why we do first << then >>
        io.out.mantissa := result_mantissa_shifted_subnormal(
          gen_fp.mantissa_width - 1,
          0
        )
        io.out.exponent := 0.U
        io.out.sign := b.sign
      }.otherwise {
        // normal
        io.out.mantissa := result_mantissa_shifted_normal(
          gen_fp.mantissa_width - 1,
          0
        )
        io.out.exponent := b.exponent - shift + 1.U
        io.out.sign := b.sign
      }
    }
  }
}

object Add {
  def apply(a: FloatingPoint, b: FloatingPoint, combinational: Boolean = false)(
      implicit fp: FloatingPoint
  ): FloatingPoint = {
    val adder = Module(new Add(fp, combinational))
    adder.io.in_a := a
    adder.io.in_b := b
    adder.io.out
  }
}
