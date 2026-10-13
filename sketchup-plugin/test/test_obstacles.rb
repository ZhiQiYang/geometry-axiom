# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../geometry_framing/su/obstacles'
require_relative '../geometry_framing/core/flat_ceiling'

# 最小 API doubles 只放在本測試命名空間；不定義全域 Sketchup/Geom，
# 不更動 Numeric，不讓障礙測試污染其他核心／座標測試。
module ObstacleFixtures
  Length = Struct.new(:value) do
    def to_mm = value
  end

  module Geometry
    class Transformation
      def initialize(offset = [0, 0, 0]) = @offset = offset
      def apply(point) = point.zip(@offset).map { |a, b| a + b }
      def *(other) = self.class.new(apply(other.apply([0, 0, 0])))
    end

    class Point
      attr_reader :coordinates
      def initialize(coordinates) = @coordinates = coordinates
      def transform(transform) = self.class.new(transform.apply(@coordinates))
      def to_a = @coordinates.map { |value| Length.new(value) }
    end

    class BoundingBox
      def initialize = @points = []
      def add(point) = @points << point.coordinates
      def empty? = @points.empty?
      def corner(index)
        Point.new((0..2).map do |axis|
          values = @points.map { |point| point[axis] }
          index[axis].zero? ? values.min : values.max
        end)
      end
    end
  end

  Layer = Struct.new(:visible, :folder) do
    def visible? = visible
  end
  Vertex = Struct.new(:position)
  Model = Struct.new(:entities)

  module API
    class Entity
      attr_accessor :name, :layer, :hidden, :dictionary
      attr_reader :persistent_id
      def initialize(id, name = '')
        @persistent_id, @name = id, name
        @layer = Layer.new(true, nil)
        @hidden = false
      end
      def hidden? = @hidden
      def attribute_dictionary(name, create = false)
        raise '障礙讀取不得新增屬性字典' if create
        name == 'GeometryFraming' ? @dictionary : nil
      end
    end

    class Edge < Entity
      attr_reader :vertices
      def initialize(id, vertices)
        super(id)
        @vertices = vertices
      end
    end

    class Face < Entity
      attr_accessor :connected
      attr_reader :vertices
      def initialize(id, vertices)
        super(id)
        @vertices = vertices
        @connected = [self]
      end
      def all_connected = @connected
    end

    class Group < Entity
      attr_accessor :entities, :transformation
      def initialize(id, name, entities, offset = [0, 0, 0])
        super(id, name)
        @entities = entities
        @transformation = Geometry::Transformation.new(offset)
      end
      def bounds
        bounds = Geometry::BoundingBox.new
        @entities.each do |entity|
          if entity.respond_to?(:vertices)
            entity.vertices.each { |vertex| bounds.add(vertex.position.transform(@transformation)) }
          else
            (0..7).each { |index| bounds.add(entity.bounds.corner(index).transform(@transformation)) } unless entity.bounds.empty?
          end
        end
        bounds
      end
    end

    # 真實 ComponentInstance 沒有 Group#entities；強制走 definition.entities。
    class ComponentInstance < Entity
      attr_reader :transformation
      def initialize(id, name, entities, offset = [0, 0, 0])
        super(id, name)
        @definition = Struct.new(:entities, :name).new(entities, '測試元件定義')
        @transformation = Geometry::Transformation.new(offset)
      end
      def definition = @definition
      def bounds
        proxy = Group.new(persistent_id, name, @definition.entities)
        proxy.transformation = @transformation
        proxy.bounds
      end
    end
  end

  module_function

  def prism(id, minimum = [100, 100, 2490], maximum = [400, 400, 2800])
    vertices = (0..7).map do |i|
      Vertex.new(Geometry::Point.new((0..2).map { |axis| i[axis].zero? ? minimum[axis] : maximum[axis] }))
    end
    sides = [[0, 1, 3, 2], [4, 5, 7, 6], [0, 1, 5, 4], [2, 3, 7, 6], [0, 2, 6, 4], [1, 3, 7, 5]]
    faces = sides.each_with_index.map { |indices, i| API::Face.new(id + i, indices.map { |index| vertices[index] }) }
    pairs = sides.flat_map { |indices| indices.each_with_index.map { |a, i| [a, indices[(i + 1) % 4]].sort } }.uniq
    edges = pairs.each_with_index.map { |pair, i| API::Edge.new(id + 10 + i, pair.map { |index| vertices[index] }) }
    connected = faces + edges
    faces.each { |face| face.connected = connected }
    connected
  end

  def ceiling
    vertices = [[0, 0, 2500], [5000, 0, 2500], [5000, 4800, 2500], [0, 4800, 2500]].map do |point|
      Vertex.new(Geometry::Point.new(point))
    end
    API::Face.new(1, vertices)
  end

  def group(id, name, **options)
    minimum = options.fetch(:min, [100, 100, 2490])
    maximum = options.fetch(:max, [400, 400, 2800])
    API::Group.new(id, name, prism(id * 100, minimum, maximum), options.fetch(:offset, [0, 0, 0]))
  end
end

class ObstaclesTest < Minitest::Test
  Fixtures = ObstacleFixtures
  Obstacles = GeometryFraming::SU::Obstacles

  def collect(entities, face: Fixtures.ceiling, selected_path: [])
    Obstacles.collect(Fixtures::Model.new(entities), selected_path: selected_path, face: face,
                      inverse: Fixtures::Geometry::Transformation.new,
                      api: Fixtures::API, geometry: Fixtures::Geometry)
  end

  def test_previous_plugin_result_is_not_a_beam_on_rerun
    face = Fixtures.ceiling
    previous = Fixtures.group(10, '使用者改過群組名稱', min: [0, 0, 2500], max: [5000, 4800, 2539])
    previous.dictionary = { 'mode' => 'flat', 'unit' => 'mm' }
    beam = Fixtures.group(20, '真正 RC 樑', min: [100, 100, 2600], max: [400, 400, 2800])
    obstacles = collect([face, previous, beam], face: face)
    assert_equal 1, obstacles.length, 'P076 M2 自產物排除：前次下角材群組不可在同面重跑時被當成樑'
    result = GeometryFraming::Core::FlatCeiling.build(rings: [[[0, 0], [5000, 0], [5000, 4800], [0, 4800]]],
                                                    params: { corner: 'tr' }, obstacles: obstacles)
    assert result[:checks].find { |item| item[:id].to_s == 'obstacles' }[:ok], 'P076 M2 自產物排除：換起鋪角重跑不應誤要求降到 2461'
    assert_nil result[:suggested_ceil], 'P076 M2 自產物排除：前次作品不可產生降板建議'
    previous.dictionary = nil
    previous.name = '下角材 平釘 2026-10-13'
    assert_equal 2, collect([face, previous, beam], face: face).length, 'P076 M2 自產物排除：不可只因名稱相似而漏掉真正障礙'
  end

  def test_hidden_or_tag_disabled_entities_are_excluded
    beam = Fixtures.group(20, '可見樑')
    hidden = Fixtures.group(30, '隱藏樑')
    hidden.hidden = true
    tagged_off = Fixtures.group(40, '關閉 Tag 的樑')
    tagged_off.layer.visible = false
    output = collect([beam, hidden, tagged_off])
    assert_equal 1, output.length, 'P076 M2 可見性：隱藏及關閉 Tag 的實體不得算障礙'
    assert_includes output.first[:id], '可見樑', 'P076 M2 可見性：可見的真正樑仍必須被保留'
  end

  def test_hierarchy_visibility_and_tag_folder_visibility_are_respected
    face = Fixtures.ceiling
    visible = Fixtures.group(20, '可見樑')
    hidden_parent = Fixtures::API::Group.new(30, '隱藏父群組', [Fixtures.group(31, '可見子樑')])
    hidden_parent.hidden = true
    tag_parent = Fixtures::API::Group.new(40, '關閉 Tag 父群組', [Fixtures.group(41, '可見子樑')])
    tag_parent.layer.visible = false
    folder_child = Fixtures.group(50, '關閉上層 Tag 資料夾的樑')
    folder_child.layer.folder = Fixtures::Layer.new(true, Fixtures::Layer.new(false, nil))
    building = Fixtures::API::Group.new(90, '二樓', [face, visible, hidden_parent, tag_parent, folder_child])
    output = collect([building], face: face, selected_path: [building])
    assert_equal 1, output.length, 'P076 M2 可見性：父群組隱藏／Tag 關閉／祖先 Tag 資料夾關閉必須一路生效'
    assert_includes output.first[:id], '可見樑'
  end

  def test_hidden_or_generated_descendants_do_not_expand_container_bounds
    visible = Fixtures.group(20, '真正高樑', min: [100, 100, 2600], max: [400, 400, 2800])
    hidden = Fixtures.group(30, '隱藏低樑', min: [0, 0, 2000], max: [5000, 4800, 2500])
    hidden.hidden = true
    generated = Fixtures.group(40, '舊作品', min: [0, 0, 2500], max: [5000, 4800, 2539])
    generated.dictionary = { 'mode' => 'flat' }
    container = Fixtures::API::ComponentInstance.new(90, '巢狀結構', [visible, hidden, generated], [1000, 2000, 0])
    output = collect([container])
    assert_equal 1, output.length, 'P076 M2 保守包圍盒：仍保留容器為單一障礙，不自行拆開其材料分類'
    assert_equal [1100, 2100, 2600], output.first[:min], 'P076 M2 可見性：隱藏／自產後代不能把容器包圍盒擴大到天花高度'
    assert_equal [1400, 2400, 2800], output.first[:max]
  end

  def test_container_envelope_is_conservative_and_reports_full_named_path
    face = Fixtures.ceiling
    walls = Fixtures::API::Group.new(30, '四面牆容器', [
      Fixtures.group(31, '西牆', min: [-100, -100, 0], max: [0, 4900, 2800]),
      Fixtures.group(32, '東牆', min: [5000, -100, 0], max: [5100, 4900, 2800]),
      Fixtures.group(33, '南牆', min: [0, -100, 0], max: [5000, 0, 2800]),
      Fixtures.group(34, '北牆', min: [0, 4800, 0], max: [5000, 4900, 2800])
    ])
    building = Fixtures::API::Group.new(10, 'A 棟', [face, walls])
    output = collect([building], face: face, selected_path: [building])
    assert_equal 1, output.length, 'P076 M2 保守包圍盒：四面牆仍以整個容器 bbox 回報，不擅自當成無障礙'
    assert_equal [-100, -100, 0], output.first[:min]
    assert_equal [5100, 4900, 2800], output.first[:max]
    assert_includes output.first[:id], 'A 棟 (#10) / 四面牆容器 (#30)', 'P076 M2 診斷路徑：必須可從名稱與完整 instance path 找到障礙'
    result = GeometryFraming::Core::FlatCeiling.build(rings: [[[0, 0], [5000, 0], [5000, 4800], [0, 4800]]], obstacles: output)
    detail = result[:checks].find { |item| item[:id].to_s == 'obstacles' }[:detail]
    assert_includes detail, 'A 棟 (#10) / 四面牆容器 (#30)', 'P076 M2 診斷路徑：實際碰撞訊息須保留名稱與路徑'
  end

  def test_loose_connected_beam_is_kept_once_and_source_face_is_excluded
    face = Fixtures.ceiling
    beam = Fixtures.prism(200)
    output = collect([face, *beam], face: face)
    assert_equal 1, output.length, 'P076 M2 未分組障礙：連通六面樑須合成一筆，不能漏掉或六次重複'
    assert_equal [100, 100, 2490], output.first[:min]
    assert_equal [400, 400, 2800], output.first[:max]
  end
end
