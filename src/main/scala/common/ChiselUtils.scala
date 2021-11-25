package common

import chisel3._

object ChiselUtils {
  /** @param a
    * @param b
    * @return $a-b$
    */
  def uint_diff(a: UInt, b: UInt): SInt = {
    Mux(
      a > b,
      (a -% b).asSInt(),
      -((b -% a).asSInt())
    )
  }

  def uint_diff_saturate(a: UInt, b: UInt): UInt = {
    Mux(
      a > b,
      a -% b,
      0.U
    )
  }
}
