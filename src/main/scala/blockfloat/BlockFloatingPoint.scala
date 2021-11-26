package blockfloat

import chisel3._

/** Fixed point number with exponent.
  *
  * @param exponent_width
  *   Exponent width (including the sign bit).
  * @param mantissa_width
  *   Mantissa width (including the sign bit).
  */
case class FixedPointWithExponent(
    val exponent_width: Int,
    val mantissa_width: Int
) extends Bundle {
  val exponent = SInt(exponent_width.W)
  val mantissa = SInt(mantissa_width.W)

  override def toString(): String = s"fxe${exponent_width}m${mantissa_width}"
}

/** Block floating point.
  *
  * @param block_size
  *   Block size.
  * @param exponent_width
  *   Exponent width (including the sign bit).
  * @param mantissa_width
  *   Mantissa width (including the sign bit).
  */
case class BlockFloatingPoint(
    val block_size: Int,
    val exponent_width: Int,
    val mantissa_width: Int
) extends Bundle {
  val exponent = SInt(exponent_width.W)
  val mantissas = Vec(block_size, SInt(mantissa_width.W))

  def as_fixed_point_with_exponent =
    FixedPointWithExponent(exponent_width, mantissa_width)

  override def toString(): String =
    s"bfpn${block_size}e${exponent_width}m${mantissa_width}"
}
