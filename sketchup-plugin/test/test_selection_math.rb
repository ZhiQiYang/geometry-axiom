# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../geometry_framing/su/selection'

class SelectionMathTest < Minitest::Test
  Selection = GeometryFraming::SU::Selection
  FakeVertex = Struct.new(:persistent_id)
  FakeEdge = Struct.new(:vertices)

  def chain
    # 尾端 PID 比起端小；若不小心恢復 min_by(&:persistent_id)，會反轉方向。
    vertices = [400, 12, 900, 25, 1].map { |id| FakeVertex.new(id) }
    edges = vertices.each_cons(2).with_index.map { |pair, index| FakeEdge.new(index.even? ? pair.reverse : pair) }
    [vertices, edges]
  end

  def test_profile_chain_uses_explicit_start_endpoint_in_both_directions
    vertices, edges = chain
    forward = Selection.ordered_vertices(edges, start_vertex_id: vertices.first.persistent_id)
    assert_equal vertices, forward, '斷面起點：必須從使用者明示的端點開始，不能以較小 PID 決定方向'
    reversed = Selection.ordered_vertices(edges, start_vertex_id: vertices.last.persistent_id)
    assert_equal vertices.reverse, reversed, '斷面起點：明示另一端時必須完整反向，不能擅自選方向'
  end

  def test_profile_chain_selection_order_does_not_override_explicit_start
    vertices, edges = chain
    edges.permutation.each do |selection|
      assert_equal vertices, Selection.ordered_vertices(selection, start_vertex_id: vertices.first.persistent_id),
                   '斷面起點：所有選邊順序都必須遵守同一個明示端點'
      assert_equal vertices.reverse, Selection.ordered_vertices(selection, start_vertex_id: vertices.last.persistent_id),
                   '斷面起點：選邊順序不得改變使用者指定的反向搭接'
    end
  end

  def test_profile_chain_rejects_missing_start_instead_of_guessing_from_pid
    _vertices, edges = chain
    assert_raises(GeometryFraming::SU::InputError, '斷面起點：沒有明示起點時必須拒絕，不能按 PID 猜') do
      Selection.ordered_vertices(edges)
    end
    assert_raises(GeometryFraming::SU::InputError, '斷面起點：nil 也不表示可自動選第一個端點') do
      Selection.ordered_vertices(edges, start_vertex_id: nil)
    end
  end

  def test_profile_chain_rejects_interior_or_unknown_start_vertex
    vertices, edges = chain
    [vertices[1].persistent_id, vertices[2].persistent_id, vertices[3].persistent_id, 999_999].each do |id|
      assert_raises(GeometryFraming::SU::InputError, '斷面起點：只有所選折線的兩個端點可作明示起點') do
        Selection.ordered_vertices(edges, start_vertex_id: id)
      end
    end
  end

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
