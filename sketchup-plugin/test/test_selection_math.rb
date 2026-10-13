# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../geometry_framing/su/selection'

class SelectionMathTest < Minitest::Test
  Selection = GeometryFraming::SU::Selection

  def test_rotated_translated_l_shape_remains_exactly_orthogonal_after_projection
    angle = Math::PI / 180
    cosine, sine = Math.cos(angle), Math.sin(angle)
    original = [[0, 0], [5000, 0], [5000, 3000], [3200, 3000], [3200, 4800], [0, 4800]]
    world = original.map do |x, y|
      [(10_000 + x * cosine + y * sine).round(6), (20_000 + x * sine - y * cosine).round(6), 2500]
    end
    projected = world.map { |point| [Selection.dot(point, [cosine, sine, 0]), Selection.dot(point, [sine, -cosine, 0])] }
    minx, miny = (0..1).map { |axis| projected.map { |point| point[axis] }.min }
    points = Selection.snap_axes(projected.map { |x, y| [x - minx, y - miny] })
    points.each_with_index do |a, index|
      b = points[(index + 1) % points.length]
      assert(a[0] == b[0] || a[1] == b[1], 'SU_COORDINATES：水平面旋轉 1° 後仍须精確正交，不能因浮點漂移被 core 拒絕')
    end
    original.zip(points).each do |expected, actual|
      expected.zip(actual).each { |a, b| assert_in_delta(a, b, Selection::TOL, 'SU_COORDINATES：不能改動實際尺寸') }
    end
  end

  def test_profile_shared_axis_values_and_rc_zero_survive_numeric_drift
    points = Selection.snap_axes([[467.000002, -0.000001], [466.999999, 148.000002], [743, 147.999999]])
    assert_equal(0.0, points[0][1], 'SU_COORDINATES：RC 基準須維持精確零')
    assert_equal(points[0][0], points[1][0], 'SU_COORDINATES：斷面直立段須精確共線')
    assert_equal(points[1][1], points[2][1], 'SU_COORDINATES：斷面水平段須精確共線')
  end

  def test_real_nonorthogonal_edge_is_not_snapped_to_a_rule
    points = Selection.snap_axes([[0, 0], [5000, 0.001]])
    refute_equal(points[0][1], points[1][1], 'SU_COORDINATES：超出數值容差的斜邊不得被改成正交')
  end
end
