# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../geometry_framing/su/selection'
require_relative '../geometry_framing/core/flat_ceiling'

class SelectionMathTest < Minitest::Test
  Selection = GeometryFraming::SU::Selection
  FakeVertex = Struct.new(:persistent_id)
  FakeEdge = Struct.new(:vertices)

  def rotated_world(ring, degrees)
    angle = degrees * Math::PI / 180.0
    cosine, sine = Math.cos(angle), Math.sin(angle)
    # 獨立建立世界座標夾具；6位小數重現 SketchUp 讀取的 mm 精度。
    [ring.map do |x, y|
      [(10_000 + x * cosine + y * sine).round(6),
       (20_000 + x * sine - y * cosine).round(6), 2500]
    end]
  end

  def flat_inventory(rings)
    result = GeometryFraming::Core::FlatCeiling.build(rings: rings)
    {
      counts: result[:solids].group_by { |solid| solid[:role] }.transform_values(&:length),
      seams: [result[:la][:seams], result[:lb][:seams]],
      # 以板寬A／板長B座標比較面材；換房間局部X/Y不應令預期也跟著錯。
      boards: result[:solids].select { |solid| solid[:role] == 'board' }.map do |solid|
        solid[:boxes].map do |box|
          result[:A] == 'x' ? box : [box[1], box[0], box[2], box[4], box[3], box[5]]
        end
      end
    }
  end

  def test_d1_integer_mm_longest_edge_projection_notch_3000_angles
    original = [[0, 0], [12_000, 0], [12_000, 8000], [6030, 8000],
                [6030, 7970], [6000, 7970], [6000, 8000], [0, 8000]]
    failures = []
    3000.times do |index|
      degrees = index * 360.0 / 3000
      begin
        rings = Selection.project_flat_rings(rotated_world(original, degrees))[:rings]
        failures << [degrees, '座標不等於整數 mm 夾具'] unless rings == [original]
      rescue GeometryFraming::SU::InputError => error
        failures << [degrees, error.message]
      end
    end
    assert failures.empty?, "D1 整數 mm：12000×8000／30 mm 凹口旋轉3000角度須0誤拒且尺寸完全相同；失敗#{failures.length}，前例#{failures.first(4).inspect}"
  end

  def test_d1_integer_mm_projection_3664_by_3668_400_angles_keeps_inventory
    original = [[0, 0], [3664, 0], [3664, 3668], [0, 3668]]
    # 最長邊沿原本的 Y：新平面 X=3668、Y=3664；預期不用投影helper計算。
    expected = flat_inventory([[[0, 0], [3668, 0], [3668, 3664], [0, 3664]]])
    failures = []
    400.times do |index|
      degrees = index / 10.0
      begin
        rings = Selection.project_flat_rings(rotated_world(original, degrees))[:rings]
        actual = flat_inventory(rings)
        failures << [degrees, actual[:counts], actual[:seams]] unless actual == expected
      rescue GeometryFraming::SU::InputError, ArgumentError => error
        failures << [degrees, error.message]
      end
    end
    assert failures.empty?, "D1 整數 mm：3664×3668含0.2°在400角度的數量／縫／面材須與未旋轉相同；失敗#{failures.length}，前例#{failures.first(4).inspect}"
  end

  def test_d1_equal_length_edges_keep_loop_direction_across_full_rotation
    original = [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]
    failures = []
    400.times do |index|
      degrees = index * 360.0 / 400
      actual = Selection.project_flat_rings(rotated_world(original, degrees))
      failures << degrees unless actual[:rings] == [original]
      expected_x = [Math.cos(degrees * Math::PI / 180), Math.sin(degrees * Math::PI / 180), 0]
      failures << [degrees, 'X 軸翻轉'] unless Selection.dot(actual[:xaxis], expected_x) > 0.999_999
    end
    assert failures.empty?, "D1 整數 mm：等長邊不可因微小誤差輪流中選或翻轉有向軸；前例#{failures.first(4).inspect}"
  end

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
    points = Selection.project_flat_rings([world])[:rings].first
    points.each_with_index do |a, index|
      b = points[(index + 1) % points.length]
      assert(a[0] == b[0] || a[1] == b[1], 'SU_COORDINATES：水平面旋轉 1° 後仍须精確正交，不能因浮點漂移被 core 拒絕')
    end
    original.zip(points).each do |expected, actual|
      expected.zip(actual).each { |a, b| assert_in_delta(a, b, Selection::TOL, 'SU_COORDINATES：不能改動實際尺寸') }
    end
  end

  def test_profile_shared_axis_values_and_rc_zero_survive_numeric_drift
    points = Selection.integer_projection([[467.000002, -0.000001], [466.999999, 148.000002], [743, 147.999999]])
    assert_equal(0.0, points[0][1], 'SU_COORDINATES：RC 基準須維持精確零')
    assert_equal(points[0][0], points[1][0], 'SU_COORDINATES：斷面直立段須精確共線')
    assert_equal(points[1][1], points[2][1], 'SU_COORDINATES：斷面水平段須精確共線')
  end

  def test_real_nonorthogonal_edge_is_not_rounded_to_a_rule
    error = assert_raises(GeometryFraming::SU::InputError) do
      Selection.integer_projection([[0, 0.1], [5000, 0.7]])
    end
    assert_match(/取整前.*0.5 mm/, error.message, 'D1 整數 mm：取整前偏軸誤差超過0.5mm須拒絕')
  end

  def test_d1_integer_mm_projection_uses_half_mm_boundary_for_native_input_only
    assert_equal [[0, 0], [5000, 0]], Selection.integer_projection([[0, -0.25], [5000, 0.25]]),
                 'D1 整數 mm：0.5mm內的原生輸入投影可落到整數座標'
    assert_equal [[2, -2], [5000, -2]], Selection.integer_projection([[1.5, -1.5], [4999.5, -1.5]]),
                 'D1 整數 mm：半mm依Ruby round取整，僅限原生輸入邊界'
  end
end
