package emitter

import chisel3._
import chisel3.stage._
import float._
import blockfloat._
import java.io._

class EmitterBase extends App {
  val chisel_stage = new ChiselStage

  def create_directory(path: String): Unit = {
    val dir = new File(path)
    if (!dir.exists())
      dir.mkdirs()
  }

  def emit_verilog(name: String, module_gen: => Module): Unit = {
    println(s"Generating ${name}")
    val target_dir = s"chisel3_generated/${name}"
    create_directory(target_dir)
    chisel_stage.emitVerilog(
      module_gen,
      Array(
        "--target-dir",
        target_dir,
        "--full-stacktrace"
      )
    )
  }
}

object Emitter extends EmitterBase {
  def emit_fx_ops(): Unit = {
    for (i <- (1 to 16)) {
      emit_verilog(s"op_u${i}_add", new generic.Add(UInt(i.W)))
      emit_verilog(
        s"op_u${i}_mult",
        new generic.Multiply(UInt(i.W), UInt((2 * i).W))
      )
      emit_verilog(s"op_s${i}_add", new generic.Add(SInt(i.W)))
      emit_verilog(
        s"op_s${i}_mult",
        new generic.Multiply(SInt(i.W), SInt((2 * i).W))
      )
    }
  }

  def emit_fp_ops(): Unit = {
    def emit_one(gen_fp: FloatingPoint): Unit = {
      emit_verilog(s"op_${gen_fp}_add", new float.Add(gen_fp, false))
      emit_verilog(s"op_${gen_fp}_mult", new float.Multiply(gen_fp))
    }

    emit_one(FloatingPoint.ieee_fp16)
    emit_one(FloatingPoint.ieee_fp32)
    emit_one(FloatingPoint.ieee_fp64)
    emit_one(FloatingPoint.fp18)
    emit_one(FloatingPoint.bfloat16)
  }

  def emit_fxe_to_fp(): Unit = {
    def emit_one(
        gen_fxe: FixedPointWithExponent,
        gen_fp: FloatingPoint
    ): Unit = {
      emit_verilog(
        s"fxe2fp_${gen_fxe}_${gen_fp}",
        new FixedPointWithExponentToFloatingPoint(gen_fxe, gen_fp)
      )
    }

    for (i <- (1 to 8)) {
      // It does not make any sense to choose an exponent width larger than
      // the floating point format's exponent width.
      emit_one(FixedPointWithExponent(10, 2 * i), FloatingPoint.bfloat16)
    }
  }

  def emit_fp_to_bfp(): Unit = {
    def emit_one(
        gen_fp: FloatingPoint,
        gen_bfp: BlockFloatingPoint
    ): Unit = {
      emit_verilog(
        s"fp2bfp_${gen_fp}_${gen_bfp}",
        new FloatingPointToBlockFloatingPoint(gen_fp, gen_bfp)
      )
    }

    val exponent_width = 10

    val block_sizes = Array(2, 4, 6, 32)
    val mantissa_widths = Array(2, 3, 4, 5, 6, 7, 8)

    block_sizes.zip(mantissa_widths).foreach {
      case (block_size, mantissa_width) =>
        emit_one(
          FloatingPoint.bfloat16,
          BlockFloatingPoint(block_size, exponent_width, mantissa_width)
        )
    }
  }

  def emit_accum(): Unit = {
    def emit_one(gen_fp: FloatingPoint): Unit = {
      emit_verilog(s"accum_${gen_fp}", new float.Accumulator(gen_fp))
    }

    emit_one(FloatingPoint.ieee_fp16)
    emit_one(FloatingPoint.ieee_fp32)
    emit_one(FloatingPoint.ieee_fp64)
    emit_one(FloatingPoint.fp18)
    emit_one(FloatingPoint.bfloat16)
  }

  emit_fx_ops()
  emit_fp_ops()
  emit_fxe_to_fp()
  emit_fp_to_bfp()
  emit_accum()
}
