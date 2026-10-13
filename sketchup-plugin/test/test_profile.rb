# frozen_string_literal: true

require_relative 'test_helper'

class ProfileTest < Minitest::Test
  include FramingTestSupport

  CHECK_IDS = %i[profile_orthogonal profile_rc profile_boards profile_longs profile_spacing profile_inside profile_overlap].freeze

  def test_cove_acceptance_counts_and_all_seven_checks
    result = profile(ORACLE[:profiles].first)
    assert_equal [4, 6, 4], %i[boards longs ribs].map { |key| result[key].length }, '間接照明槽：4 面材、6 縱向料、4 斷面橫撐'
    assert_equal 7, result[:checks].length, '間接照明槽必須顯示 7 項規則檢查'
    assert result[:checks].all? { |check| check[:ok] }, '間接照明槽 7 項規則必須全過'
    assert_equal({ 'board' => 4, 'long' => 6, 'rib' => 28 }, result[:solids].group_by { |solid| solid[:role] }.transform_values(&:length), 'pf3D：L=2400 分 6 段、首末皆有橫撐，共 7 排 × 4 = 28 支')
  end

  ORACLE[:profiles].each do |fixture|
    define_method("test_demo_profile_#{fixture[:name]}") do
      result = profile(fixture)
      %i[boards longs ribs].each { |key| assert_oracle fixture[key], result[key], "#{fixture[:name]} / #{key}" }
      CHECK_IDS.each_with_index do |id, index|
        assert_equal fixture[:checks][index][:ok], rule(result, id)[:ok], "#{fixture[:name]} / #{id}"
      end
      # 原始 box3 的平面 y 會再取負；將 demo 的絕對樓板 2800 換成 core 局部原點。
      expected = fixture[:boxes].map { |x0, y0, x1, y1, z0, z1| [x0, -y1, z0 - 2800, x1, -y0, z1 - 2800] }
      actual = result[:solids].flat_map { |solid| solid[:boxes] }
      assert_oracle expected, actual, "#{fixture[:name]} / pf3D 所有實體盒"
    end
  end

  def test_structure_flip_must_not_silently_claim_inside
    fixture = ORACLE[:profiles].find { |item| item[:name] == 'flipped' }
    result = profile(fixture)
    refute rule(result, :profile_inside)[:ok], '結構換邊後凸出原閉合輪廓，必須忠實回報輪廓內檢查失敗'
    refute result[:valid], '失敗檢查不得被當成有效模型'
  end

  def test_extrusion_keeps_panels_and_longs_continuous
    result = profile(ORACLE[:profiles].first)
    result[:solids].select { |solid| %w[board long].include?(solid[:role]) }.each do |solid|
      assert_equal 1, solid[:boxes].length, '面材與縱向料沿 L 必須整支連續'
      assert_equal [0, 2400], solid[:boxes].first.values_at(1, 4), '面材與縱向料須涵蓋完整 L'
    end
  end
end
