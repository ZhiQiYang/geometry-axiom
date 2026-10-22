# frozen_string_literal: true

require 'json'
require 'minitest/autorun'
require_relative '../geometry_framing/core/panel_axis'
require_relative '../geometry_framing/core/flat_ceiling'
require_relative '../geometry_framing/core/profile'

module FramingTestSupport
  ORACLE = JSON.parse(File.read(File.join(__dir__, 'fixtures/demo_oracle.json'), encoding: 'UTF-8'), symbolize_names: true)

  def flat(fixture, params = {}, obstacles: [], **overrides)
    GeometryFraming::Core::FlatCeiling.build(
      id: fixture[:id], rings: fixture[:rings], params: fixture[:params].merge(params).merge(overrides), obstacles: obstacles
    )
  end

  def profile(fixture)
    GeometryFraming::Core::Profile.build(points: fixture[:points], params: fixture[:params])
  end

  def rule(result, id)
    result.fetch(:checks).find { |check| check.fetch(:id).to_s == id.to_s } || flunk("缺少規則檢查 #{id}")
  end

  # 比對獨立 demo 的數字，允許浮點運算末位誤差；訊息指出案例與欄位。
  # 只比較 oracle 已記錄的欄位，插件可額外提供 SketchUp 所需 metadata。
  def assert_oracle(expected, actual, location)
    case expected
    when Hash
      assert_kind_of Hash, actual, location
      expected.each do |key, value|
        assert actual.key?(key), "#{location} 缺少 #{key}"
        assert_oracle(value, actual[key], "#{location}.#{key}")
      end
    when Array
      assert_kind_of Array, actual, location
      assert_equal expected.length, actual.length, "#{location} 數量"
      expected.each_with_index { |value, i| assert_oracle(value, actual[i], "#{location}[#{i}]") }
    when Numeric
      assert_in_delta expected, actual, 1e-8, location
    when NilClass
      assert_nil actual, location
    else
      assert_equal expected, actual, location
    end
  end
end
