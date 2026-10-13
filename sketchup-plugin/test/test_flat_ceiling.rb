# frozen_string_literal: true

require_relative 'test_helper'

class FlatCeilingTest < Minitest::Test
  include FramingTestSupport

  CHECK_IDS = %i[start_full end_faces equal_marks spacing seam_bearing primary_continuity obstacles edge_shift].freeze

  def test_five_demo_room_totals
    assert_equal [84, 57, 48, 28, 32], ORACLE[:flats].map { |fixture| flat(fixture)[:members].length }, '五個 demo 房間構件總數'
  end

  ORACLE[:flats].each do |fixture|
    define_method("test_demo_room_#{fixture[:id]}_geometry") do
      result = flat(fixture)
      assert_oracle fixture[:members], result[:members], "#{fixture[:id]} 構件"
      assert_oracle fixture[:la], result[:la], "#{fixture[:id]} 板寬方向"
      assert_oracle fixture[:lb], result[:lb], "#{fixture[:id]} 板長方向"
      assert_oracle fixture[:lines], result[:lines], "#{fixture[:id]} 記號與補縫"
      assert_equal fixture[:clashes], result[:clashes], "#{fixture[:id]} 主支衝突"
      expected_boxes = fixture[:boxes].map { |x0, y0, x1, y1, z0, z1| [x0, y0, z0, x1, y1, z1] }
      assert_oracle expected_boxes, result[:solids].flat_map { |solid| solid[:boxes] }, "#{fixture[:id]} 3D 實體與端部讓位"
      bad_ends = GeometryFraming::Core::FlatCeiling.end_faces(result).map { |ending| { id: ending[:m][:id], e: ending[:e], col: ending[:col] } }
      assert_oracle fixture[:badEnds], bad_ends, "#{fixture[:id]} 端面"
      CHECK_IDS.each_with_index do |id, index|
        assert_equal fixture[:checks][index][:ok], rule(result, id)[:ok], "#{fixture[:id]} / #{id}"
      end
    end
  end

  ORACLE[:variants].each do |fixture|
    define_method("test_demo_variant_#{fixture[:name]}") do
      result = flat(fixture)
      assert_oracle fixture[:members], result[:members], "#{fixture[:name]} 構件"
      assert_oracle fixture[:lines], result[:lines], "#{fixture[:name]} 記號"
      assert_equal fixture[:clashes], result[:clashes], "#{fixture[:name]} 主支衝突"
      expected_boxes = fixture[:boxes].map { |x0, y0, x1, y1, z0, z1| [x0, y0, z0, x1, y1, z1] }
      assert_oracle expected_boxes, result[:solids].flat_map { |solid| solid[:boxes] }, "#{fixture[:name]} 3D 實體與端部讓位"
      bad_ends = GeometryFraming::Core::FlatCeiling.end_faces(result).map { |ending| { id: ending[:m][:id], e: ending[:e], col: ending[:col] } }
      assert_oracle fixture[:badEnds], bad_ends, "#{fixture[:name]} 端面"
      CHECK_IDS.each_with_index do |id, index|
        assert_equal fixture[:checks][index][:ok], rule(result, id)[:ok], "#{fixture[:name]} / #{id}"
      end
    end
  end

  def test_living_room_marks_are_integer_modulus_and_last_is_shifted
    result = flat(ORACLE[:flats].first)
    assert_equal [365, 731, 1098, 1464, 1831, 2197, 2563, 2930, 3296, 3663, 4029, 4395, 4759], result[:lines].map { |line| line[:t] }, '記號：由縫中心延續模數、取整數，最後收邊往內挪'
    assert rule(result, :seam_bearing)[:ok], '板端縫兩側承接至少 8 mm'
    assert rule(result, :spacing)[:ok], '副支中心間距不得超過 450 mm'
  end

  def test_column_edge_rule
    fixture = ORACLE[:flats].first
    result = flat(fixture)
    column_edges = result[:members].select { |member| member[:role] == 'wall' && member[:ri].positive? }
    assert_equal 4, column_edges.length, '規則：柱邊料，獨立柱四邊必須各有一支沿邊料'
    assert rule(result, :end_faces)[:ok], '規則：柱邊料，端面必須頂在角材上而非 RC 柱'
    disabled = flat(fixture, colEdge: false)
    refute rule(disabled, :end_faces)[:ok], '規則：柱邊料，關閉柱邊料後端面檢查必須失敗'
    assert_match(/RC.*柱|柱.*RC/, rule(disabled, :end_faces)[:detail], '規則：柱邊料，診斷必須指出 RC 柱')
  end

  def test_primary_continuity_rule
    kitchen = ORACLE[:flats].last
    result = flat(kitchen, corner: 'tr')
    assert_equal [1], result[:clashes], '規則：主支不可斷開，廚房右上第 2 道主支線會碰柱邊料'
    refute rule(result, :primary_continuity)[:ok], '規則：主支不可斷開，碰柱邊料不能當成可切斷的有效骨架'
    assert_equal [[true, 'tl'], [true, 'bl']], result[:options].map { |option| [option[:longY], option[:corner]] }, '規則：主支不可斷開，只允許左上/左下起鋪＋板長沿 Y'
    result[:options].each do |option|
      alternative = flat(kitchen, longY: option[:longY], corner: option[:corner])
      assert rule(alternative, :primary_continuity)[:ok], '規則：主支不可斷開，推薦組合本身必須不碰柱'
    end
  end

  def test_every_core_file_is_independent_of_sketchup_api
    Dir[File.expand_path('../geometry_framing/core/*.rb', __dir__)].sort.each do |path|
      refute_match(/\b(?:Sketchup|Geom)::/, File.read(path, encoding: 'UTF-8'), "純 Ruby 核心不得引用 SketchUp API：#{File.basename(path)}")
    end
  end

  def test_demo_beam_collision_and_lowered_finish_height
    fixture = ORACLE[:flats].first
    beam = { id: 'B1', min: [0, 1350, 2400], max: [5000, 1650, 2800] }
    collision = flat(fixture, ceil: 2500, obstacles: [beam])
    refute rule(collision, :obstacles)[:ok], '障礙：demo B1 樑底 2400 會碰完成面 2500 的骨架'
    assert_equal 2361, collision[:suggested_ceil], '障礙：完成面上限 = 2400 − 板厚 6 − 角材高 33'
    lowered = flat(fixture, ceil: 2361, obstacles: [beam])
    assert rule(lowered, :obstacles)[:ok], '障礙：骨架頂貼樑底時可由樑下通過'
    assert_nil lowered[:suggested_ceil], '障礙：已經通過時不應繼續要求降板'
  end

  def test_high_beam_and_obstacles_outside_room_or_inside_column_hole_do_not_collide
    bedroom = ORACLE[:flats][1]
    high = { id: 'B2', min: [6850, 0, 2600], max: [7150, 3600, 2800] }
    assert rule(flat(bedroom, obstacles: [high]), :obstacles)[:ok], '障礙：demo B2 樑底 2600 不碰骨架頂 2539'
    living = ORACLE[:flats].first
    excluded = [
      { id: '房外', min: [9000, 9000, 2300], max: [9500, 9500, 2800] },
      { id: '柱孔', min: [2310, 1310, 2300], max: [2690, 1690, 2800] }
    ]
    result = flat(living, ceil: 2500, obstacles: excluded)
    assert_empty result[:obstacles], '障礙：bbox 必須與含柱孔的房間面實際相交'
    assert rule(result, :obstacles)[:ok], '障礙：房外或柱孔內實體不得誤報碰撞'
  end
end
