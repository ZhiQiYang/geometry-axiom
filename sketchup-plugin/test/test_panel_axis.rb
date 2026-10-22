# frozen_string_literal: true

require_relative 'test_helper'

class PanelAxisTest < Minitest::Test
  include FramingTestSupport

  def test_edge_shift_rule
    axis = GeometryFraming::Core::PanelAxis.build(3700, 915, 2, 27)
    assert_equal [916, 1833, 2750, 3659], axis[:seams], '規則：收邊挪縫，最後一道縫必須從 3667 移到 3659'
    assert_equal({ from: 3667, to: 3659 }, axis[:moved], '規則：收邊挪縫，必須保留原位置與新位置')
    assert_equal [true, true, true, false, false], axis[:full], '規則：收邊挪縫，末兩片必須如實標為裁切板'
    assert_oracle ORACLE[:panel3700], axis, '房深 3700 / panelAxis'
  end

  def test_full_panel_starts_at_wall_and_only_opposite_end_is_cut
    axis = GeometryFraming::Core::PanelAxis.build(4000, 915, 2, 27)
    assert_equal [0, 915], axis[:boards].first, 'D10a：起鋪牆從 0 開始整片鋪設'
    assert_equal [916, 1833, 2750, 3667], axis[:seams], 'D10a：板縫模數 P + gap'
    assert_nil axis[:moved], '收邊足夠時不可自行挪縫'
  end

  def test_exact_period_does_not_create_an_extra_seam
    axis = GeometryFraming::Core::PanelAxis.build(1834, 915, 2, 27)
    assert_equal [916], axis[:seams], 'D10a：只在 (k + 1)T < D 時產生縫'
    assert_equal [[0, 915], [917, 1832]], axis[:boards], '忠實保留 demo 的等模數末端行為'
  end
end
