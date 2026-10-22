# frozen_string_literal: true

require 'minitest/autorun'
require 'minitest/mock'
require_relative '../geometry_framing/su/selection'
require_relative '../geometry_framing/su/builder'
require_relative '../geometry_framing/su/dialog'

class DialogReviewTest < Minitest::Test
  Entity = Struct.new(:persistent_id, :vertices, :name) do
    def typename = 'Face'
  end
  Vertex = Struct.new(:persistent_id, :position)
  Model = Struct.new(:selection, :active_path)

  def setup
    @dialog = GeometryFraming::SU::Dialog
    @saved = @dialog.instance_variables.to_h { |key| [key, @dialog.instance_variable_get(key)] }
    @dialog.instance_variables.each { |key| @dialog.remove_instance_variable(key) }
    @face = Entity.new(1, [Vertex.new(11, [0, 0, 0]), Vertex.new(12, [100, 0, 0])], '')
    @model = Model.new([@face], nil)
    @obstacle_height = 2800
    @builds, @chosen = [], []
    @valid = true
  end

  def teardown
    @dialog.instance_variables.each { |key| @dialog.remove_instance_variable(key) }
    @saved.each { |key, value| @dialog.instance_variable_set(key, value) }
  end

  def evaluated(mode:, params:, model:, start_vertex_id: nil, &chooser)
    if mode == 'profile'
      start_vertex_id ||= chooser.call([{ id: 101, point: [0, 0, 0] }, { id: 102, point: [100, 0, 0] }])
      raise GeometryFraming::SU::StartPointError, '已取消' unless start_vertex_id

      @chosen << start_vertex_id
    end
    resolved = { cap: 450.0 }.merge(params.transform_keys(&:to_sym))
    {
      snapshot: { input: { source_id: model.selection.first.persistent_id, start_vertex_id: start_vertex_id },
                  frame: [1, 0, 0, 1], obstacles: [{ height: @obstacle_height }] },
      result: { params: resolved, checks: [{ id: 'D4', ok: @valid }], valid: @valid,
                solids: [{ role: 'board', boxes: [[0, 0, 0, 100, 100, 6]] }] }
    }
  end

  def with_backend
    build = ->(**args) { @builds << args; Struct.new(:name).new('批次') }
    @dialog.stub(:evaluate, method(:evaluated)) do
      GeometryFraming::SU::Builder.stub(:generate, build) { yield }
    end
  end

  def call(generate = false, params = {}, mode = 'flat', &chooser)
    @dialog.dispatch({ mode: mode, params: params }, generate, model: @model, &chooser)
  end

  def test_generate_requires_successful_matching_preview_and_consumes_it
    with_backend do
      assert_equal 'stale', call(true)[:status]
      assert_empty @builds
      preview = call
      assert preview[:ok]
      generated = call(true, preview[:params])
      assert_equal 'generated', generated[:status]
      assert generated[:generated]
      refute generated[:ok], '規則：生成成功消耗檢查，不能連點建立兩批'
      assert_equal 1, @builds.length
      assert_equal 'stale', call(true)[:status]
      assert_equal 1, @builds.length
    end
  end

  def test_selection_change_rejects_without_waiting_for_observer
    with_backend do
      call
      @model.selection = [Entity.new(2, [], 'B')]
      rejected = call(true)
      assert_equal 'stale', rejected[:status], 'UX_STALE_SELECTION：生成必須使用成功檢查的同一選取'
      assert rejected[:preserve_result]
      refute rejected.key?(:mode), '規則：失效通知不得把使用者剛切換的模式改回舊模式'
      assert_includes rejected[:selection_label], 'B'
      refute rejected.key?(:counts), '規則：失效通知保留上一輪數量、條件、建議'
      assert_empty @builds
    end
  end

  def test_stale_selection_keeps_updating_after_generated_batch_is_undone
    updates = []
    timer = Object.new
    timer.define_singleton_method(:start_timer) { |*_args| 1 }
    timer.define_singleton_method(:stop_timer) { |_id| }
    watch = GeometryFraming::SU::SelectionWatch.new(model_provider: -> { @model }, timer_api: timer) do |model|
      updates << @dialog.invalidate_review(model: model)
    end
    with_backend do
      preview = call
      assert call(true, preview[:params])[:generated]
      @model.selection = [] # SketchUp 一次 Undo 後選取清空。
      watch.tick
      assert_equal '尚未選取', updates.last[:selection_label]
      @model.selection = [Entity.new(2, [], 'K')]
      watch.tick
      assert updates.last, 'UX_STALE_SELECTION_REFRESH：結果過期後仍須通知後續的目前選取'
      assert_includes updates.last[:selection_label], 'K'
      @model.selection = [Entity.new(3, [], 'C')]
      watch.tick
      assert_includes updates.last[:selection_label], 'C'
      watch.tick
      assert_equal 3, updates.length, '未變更時不重複通知'
      updates.each do |update|
        assert_equal 'stale', update[:status]
        assert update[:preserve_result]
        refute update[:ok]
        %i[mode params input checks counts suggested_ceil].each { |key| refute update.key?(key), "不得重設 #{key}" }
      end
      assert_equal 'stale', call(true, preview[:params])[:status]
      assert_equal 1, @builds.length, '更新目前選取不會恢復已消耗的生成授權'
    end
  ensure
    watch&.stop
  end

  def test_geometry_and_parameter_changes_are_rejected_without_observer
    with_backend do
      call
      @obstacle_height = 2600 # 同一 face ID、selection、path，但既有障礙變更。
      assert_equal 'stale', call(true)[:status], 'UX_STALE_SNAPSHOT：障礙幾何變更不可使用上一輪檢查'
      call
      assert_equal 'stale', call(true, cap: 300)[:status], 'UX_STALE_SNAPSHOT：參數變更不可使用上一輪檢查'
      call
      @face.vertices.first.position[0] = 20
      assert_equal 'stale', call(true)[:status]
      assert_empty @builds
    end
  end

  def test_failed_preview_never_authorizes_generate_and_can_become_stale
    with_backend do
      @valid = false
      refute call[:ok]
      assert_equal 'stale', @dialog.invalidate_review(model: @model)[:status]
      assert_equal 'stale', call(true)[:status]
      assert_empty @builds
    end
  end

  def test_every_profile_preview_rechooses_start_and_preserves_parameters
    with_backend do
      defaults = []
      first = call(false, { cap: 300, flip: true }, 'profile') do |_choices, previous|
        defaults << previous
        101
      end
      second = call(false, first[:params], 'profile') do |_choices, previous|
        defaults << previous
        102
      end
      assert_equal [nil, 101], defaults, 'UX_PROFILE_RESELECT：每次檢查都必須重新提供起點選擇，並預選前次起點'
      assert_equal [101, 102], @chosen
      assert_equal first[:params], second[:params]
      generated = call(true, second[:params], 'profile') { flunk '生成不能再偷偷改選起點' }
      assert generated[:generated]
      assert_equal 102, @builds.last[:input][:start_vertex_id]
    end
  end

  def test_cancelled_profile_recheck_preserves_parameters_and_previous_choice
    with_backend do
      preview = call(false, { cap: 300 }, 'profile') { 101 }
      error = nil
      capture_io { error = call(false, preview[:params], 'profile') { nil } }
      assert_equal 'error', error[:status]
      assert error[:preserve_result]
      refute error.key?(:params)
      assert_equal 'stale', call(true, preview[:params], 'profile')[:status]
      seen = nil
      call(false, preview[:params], 'profile') { |_choices, previous| seen = previous; 102 }
      assert_equal 101, seen, '規則：取消重選不會遺失上一次明示選定的起點'
    end
  end

  def test_rotated_flat_corner_mapping_uses_the_actual_frame
    length = Struct.new(:value) { def to_mm = value }
    vector = Struct.new(:values) { def to_a = values }
    frame_type = Struct.new(:origin, :xaxis, :yaxis, :zaxis)
    frame = frame_type.new(vector.new([1000, 2000, 0].map { |n| length.new(n) }),
                           vector.new([0, 1, 0]), vector.new([1, 0, 0]), vector.new([0, 0, 1]))
    input = { source: '完成面 #1', rings: [[[0, 0], [500, 0], [500, 300], [0, 300]]], ceil: 2500 }
    @dialog.describe_selection('flat', @model, { input: input, frame: frame }, {})
    assert_equal [0, 0, 500, 300], input[:bounds_mm]
    assert_equal({ x: [0, 1, 0], y: [1, 0, 0] }, input[:directions_world])
    assert_equal [1000, 2000, 2500], input[:corner_map][:tl]
    assert_equal [1300, 2500, 2500], input[:corner_map][:br]
  end
end
