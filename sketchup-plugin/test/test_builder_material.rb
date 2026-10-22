# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../geometry_framing/su/builder'

class BuilderMaterialTest < Minitest::Test
  Builder = GeometryFraming::SU::Builder

  # 只模擬 SketchUp Material / Materials 的公開讀寫契約；不定義全域 API。
  class Material
    attr_reader :name, :color, :color_writes
    attr_accessor :alpha, :texture

    def initialize(name)
      @name = name
      @color_writes = []
      @alpha = 1.0
    end

    def color=(color)
      @color_writes << color
      @color = color
    end
  end

  class Materials
    attr_reader :added

    def initialize
      @items = {}
      @added = []
    end

    def [](name) = @items[name]

    def add(name)
      unique_name = name
      suffix = 1
      while @items.key?(unique_name)
        unique_name = "#{name}#{suffix}"
        suffix += 1
      end
      @added << unique_name
      @items[unique_name] = Material.new(unique_name)
    end
  end

  Model = Struct.new(:materials)
  Instance = Struct.new(:material)

  def test_new_role_materials_receive_the_default_color_once
    model = Model.new(Materials.new)
    Builder::ROLES.each do |role, label|
      material = Builder.material(model, role)
      assert_equal "下角材 #{label}", material.name, '材質初始化：新材質仍使用各角色的既有名稱'
      assert_equal Builder::COLORS.fetch(role), material.color, '材質初始化：新材質必須套用角色預設色'
      assert_equal [Builder::COLORS.fetch(role)], material.color_writes, '材質初始化：新材質只初始化一次'
    end
    assert_equal Builder::ROLES.length, model.materials.added.length
  end

  def test_second_ceiling_keeps_the_first_ceiling_user_material_color
    model = Model.new(Materials.new)
    first_ceiling = Instance.new(Builder.material(model, 'board'))
    first_ceiling.material.color = '#FF0000'
    first_ceiling.material.alpha = 0.6
    first_ceiling.material.texture = '使用者面材紋理.png'
    writes_before_rerun = first_ceiling.material.color_writes.dup

    second_ceiling = Instance.new(Builder.material(model, 'board'))

    assert_equal '#FF0000', first_ceiling.material.color,
                 'P076 材質保留：生成第二面天花不可把第一面使用者改紅的共用材質重設為預設色'
    assert_same first_ceiling.material, second_ceiling.material, 'P076 材質保留：同名材質應沿用，不能另建重名材質迴避'
    assert_equal writes_before_rerun, first_ceiling.material.color_writes, 'P076 材質保留：重用材質時不得再次呼叫 color='
    assert_equal 0.6, first_ceiling.material.alpha, 'P076 材質保留：沿用透明度'
    assert_equal '使用者面材紋理.png', first_ceiling.material.texture, 'P076 材質保留：沿用使用者紋理'
    assert_equal ['下角材 面材'], model.materials.added, 'P076 材質保留：兩面天花只建立一份共用材質'
  end

  def test_existing_named_material_is_reused_without_any_color_write
    model = Model.new(Materials.new)
    existing = model.materials.add('下角材 主支')
    existing.color = '#112233'
    writes = existing.color_writes.dup

    assert_same existing, Builder.material(model, 'pri'), 'P076 材質保留：模型原有同名材質必須重用'
    assert_equal '#112233', existing.color, 'P076 材質保留：不得覆寫模型原有同名材質的色彩'
    assert_equal writes, existing.color_writes, 'P076 材質保留：既有材質不得再初始化'
  end
end
