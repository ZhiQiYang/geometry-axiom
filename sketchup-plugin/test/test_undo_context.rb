# frozen_string_literal: true

require 'minitest/autorun'

module UndoContextFixtures
  module Geometry
    class Transformation
      def *(other) = self
    end
  end

  class Entity
    attr_accessor :name, :layer, :transformation, :material
    attr_reader :entities
    def initialize(model)
      @model = model
      @attributes = {}
      @entities = Entities.new(model)
      @transformation = Geometry::Transformation.new
    end
    def valid? = true
    def inspect = "#<交易夾具實體 #{object_id} #{name}>"
    def set_attribute(dictionary, key, value) = @attributes[[dictionary, key]] = value
    def get_attribute(dictionary, key) = @attributes[[dictionary, key]]
  end

  class Entities < Array
    def initialize(model)
      @model = model
      super()
    end
    def add_group
      group = Entity.new(@model)
      self << group
      group
    end
    def add_instance(_definition, _transform) = add_group
  end

  class Selection < Array
    def add(items) = concat(Array(items))
  end

  class Materials < Hash
    Material = Struct.new(:color)
    def add(name) = self[name] = Material.new
  end

  class Layers < Array
    def add(name) = name
  end

  class Definitions
    def initialize(model) = @model = model
    def add(_name) = Entity.new(@model)
  end

  # 狀態式 journal：operation 內的全部變更屬於一筆 Undo；操作外切
  # active_path 另成一笔，對應本機 before/after-one 實測及官方 API 說明。
  # 不是用「程式呼叫順序符合實作」作唯一裁判，而是實際復原後比對模型狀態。
  class Model
    attr_reader :entities, :selection, :layers, :materials, :definitions, :active_path,
                :undo_history, :redo_history, :events, :input, :prior_batches

    def initialize
      @entities = Entities.new(self)
      @input = @entities.add_group
      @prior_batches = [@entities.add_group, @entities.add_group]
      @active_path = [@input]
      @selection = Selection.new([Entity.new(self)])
      @layers = Layers.new([0])
      @materials = Materials.new
      @definitions = Definitions.new(self)
      @undo_history, @redo_history, @events = [], [], []
    end

    def valid? = true

    def snapshot
      { entities: @entities.dup, path: @active_path&.dup, selection: @selection.dup }
    end

    def restore(state)
      @entities.replace(state[:entities])
      @active_path = state[:path]&.dup
      @selection.replace(state[:selection])
    end

    def active_path=(path)
      return if @active_path == path

      before = snapshot
      @events << [:path, path, !@operation.nil?]
      @active_path = path&.dup
      @selection.clear
      record(before) unless @operation
    end

    def start_operation(name, _disable_ui, _next_transparent = false, transparent = false)
      raise '測試禁止巢狀 transaction' if @operation
      raise '本批不得合併到前批的 transparent operation' if transparent

      @events << [:start, name]
      @operation = snapshot
      true
    end

    def commit_operation
      raise '沒有開啟的 operation' unless @operation

      @events << [:commit]
      record(@operation)
      @operation = nil
      true
    end

    def abort_operation
      raise '沒有開啟的 operation' unless @operation

      @events << [:abort]
      restore(@operation)
      # SketchUp 2026 原生 workflow 首敗確認：abort 會清空 Selection，
      # 即使 context 已恢復；只有生成失敗收尾需由插件重選原輸入。
      @selection.clear
      @operation = nil
      true
    end

    def record(before)
      @undo_history << { before: before, after: snapshot }
      @redo_history.clear
    end

    def undo
      item = @undo_history.pop
      return unless item

      restore(item[:before])
      @redo_history << item
    end

    def redo
      item = @redo_history.pop
      return unless item

      restore(item[:after])
      @undo_history << item
    end
  end

  # 在獨立 lexical namespace 載入原始碼，只替代交易無關的幾何建立。
  # 不替換全域 Sketchup/Geom，不污染其他測試或已載入的正式模組。
  def self.runtime
    runtime = Module.new
    runtime.const_set(:Geom, Geometry)
    %w[selection builder].each do |name|
      path = File.expand_path("../geometry_framing/su/#{name}.rb", __dir__)
      runtime.module_eval(File.read(path), path, 1)
    end
    runtime::GeometryFraming::SU::Builder.define_singleton_method(:add_boxes) { |_entities, _boxes, _untagged| nil }
    runtime::GeometryFraming::SU::Selection.define_singleton_method(:flat) do |_model, selected, path, transform|
      { selected: selected, path: path, transform: transform }
    end
    runtime
  end
end

class UndoContextTest < Minitest::Test
  def setup
    @runtime = UndoContextFixtures.runtime
    @builder = @runtime::GeometryFraming::SU::Builder
    @selection_reader = @runtime::GeometryFraming::SU::Selection
    @model = UndoContextFixtures::Model.new
    @original = @model.snapshot
  end

  def generate
    @builder.generate(mode: 'flat', model: @model, frame: UndoContextFixtures::Geometry::Transformation.new,
                      input: {}, result: { valid: true, checks: [{ ok: true }], solids: [
                        { id: 'B1', role: 'board', boxes: [[0, 0, 2500, 100, 100, 2506]],
                          section: [100, 6], length: 100, rule: '測試面材' }
                      ] })
  end

  def test_one_undo_inside_group_removes_only_latest_batch
    generated = generate
    assert_includes @model.entities, generated
    assert_equal @original[:path], @model.active_path
    assert_equal @original[:selection], @model.selection

    @model.undo

    assert_equal @original[:entities], @model.entities,
                 'UX_UNDO：群組編輯內生成後一次原生 Undo 必須移除最新一批，不能只退出編輯而保留產物'
    assert_equal @original[:path], @model.active_path, 'UX_UNDO：Undo 後保留原輸入的編輯路徑'
    @model.prior_batches.each { |prior| assert_includes @model.entities, prior, 'UX_UNDO：Undo 不得刪除前兩批' }
    assert_includes @model.entities, @model.input, 'UX_UNDO：Undo 不得刪除輸入群組'
    @model.redo
    assert_includes @model.entities, generated, 'UX_UNDO：一次 Redo 恢復同一批'
    assert_equal @original[:path], @model.active_path
  end

  def test_context_switches_are_inside_the_generation_operation
    generate
    switches = @model.events.select { |event| event.first == :path }
    assert_equal 2, switches.length
    assert switches.all? { |event| event[2] }, 'UX_UNDO：離開及恢復編輯路徑都必須在本批 start/commit 之間'
    assert_equal 1, @model.undo_history.length, 'UX_UNDO：一批只建立一筆可復原操作'
  end

  def test_reading_selection_has_no_transaction_or_context_side_effects
    before = @model.snapshot
    3.times { @selection_reader.read('flat', @model) }

    assert_empty @model.events, 'UX_READ_ONLY：預覽讀選取不得設定 active_path 或開啟／結束 operation'
    assert_equal before, @model.snapshot, 'UX_READ_ONLY：讀取不改變模型、選取或編輯路徑'
    assert_empty @model.undo_history, 'UX_READ_ONLY：讀取不得新增 Undo 紀錄'
  end

  def test_reading_selection_after_undo_keeps_redo_available
    generated = generate
    @model.undo
    redo_before = @model.redo_history.dup
    3.times { @selection_reader.read('flat', @model) }

    assert_equal redo_before, @model.redo_history, 'UX_READ_ONLY：Undo 後檢查選取不得清掉 Redo'
    @model.redo
    assert_includes @model.entities, generated, 'UX_READ_ONLY：唯讀預覽後仍可 Redo 恢復剛才產物'
  end

  def test_generation_failure_rolls_back_only_the_current_batch
    @builder.define_singleton_method(:add_boxes) { |_entities, _boxes, _untagged| raise '注入建立失敗' }
    error = assert_raises(RuntimeError) { generate }
    assert_equal '注入建立失敗', error.message
    assert_equal @original, @model.snapshot, 'UX_UNDO：中途失敗須恢復前批、輸入、選取與編輯路徑'
    assert_empty @model.undo_history, 'UX_UNDO：失敗不得遺留只有切換 context 的 Undo 紀錄'
  end
end
