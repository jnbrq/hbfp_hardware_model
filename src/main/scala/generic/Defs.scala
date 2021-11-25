package generic

import chisel3._

trait Delay {
  def delay: Int = 0
}

trait UnaryOp[T <: Data] {
  def in: T
  def out: T
}

trait BinaryOp[T <: Data] {
  def in_a: T
  def in_b: T
  def out: T
}
