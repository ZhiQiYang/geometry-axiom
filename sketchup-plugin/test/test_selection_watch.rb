# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../geometry_framing/su/selection_watch'

class SelectionWatchTest < Minitest::Test
  Entity = Struct.new(:persistent_id, :vertices, :transformation)
  Vertex = Struct.new(:persistent_id, :position)
  class Model
    attr_accessor :selection, :active_path
    attr_reader :observers
    def initialize
      @selection, @active_path, @observers = [], nil, []
    end
    def add_observer(observer) = @observers << observer
    def remove_observer(observer) = @observers.delete(observer)
  end
  class Timer
    attr_reader :stopped
    def initialize = @stopped = []
    def start_timer(_seconds, _repeat, &callback)
      @callback = callback
      7
    end
    def stop_timer(id) = @stopped << id
    def tick = @callback.call
  end

  def setup
    @had_sketchup = Object.const_defined?(:Sketchup, false)
    @old_sketchup = Object.const_get(:Sketchup) if @had_sketchup
    Object.send(:remove_const, :Sketchup) if @had_sketchup
    sketchup = Module.new
    sketchup.const_set(:ModelObserver, Class.new)
    Object.const_set(:Sketchup, sketchup)
    @model = Model.new
    @timer, @changes = Timer.new, []
    @watch = GeometryFraming::SU::SelectionWatch.new(model_provider: -> { @model }, timer_api: @timer) { |model| @changes << model }
  end

  def teardown
    @watch.stop
    Object.send(:remove_const, :Sketchup)
    Object.const_set(:Sketchup, @old_sketchup) if @had_sketchup
  end

  def test_selection_geometry_and_edit_path_invalidate
    @model.selection = [Entity.new(1, [Vertex.new(2, [0, 0, 0])], nil)]
    @timer.tick
    assert_equal 1, @changes.length
    @model.selection.first.vertices.first.position[0] = 10
    @timer.tick
    assert_equal 2, @changes.length
    @model.active_path = [Entity.new(3, [], [1, 0, 0, 1])]
    @timer.tick
    assert_equal 3, @changes.length
    @timer.tick
    assert_equal 3, @changes.length, '規則：未變更不重複發失效事件'
  end

  def test_model_observer_defers_delivery_and_suppresses_internal_operations
    observer = @model.observers.first
    observer.onTransactionCommit(@model)
    assert_empty @changes
    @timer.tick
    assert_equal 1, @changes.length
    @watch.suspend do
      observer.onActivePathChanged(@model)
      observer.onTransactionCommit(@model)
      @timer.tick
    end
    @timer.tick
    assert_equal 1, @changes.length, '規則：自身生成／暫時 context 回呼不讓成功結果立即過期'
  end

  def test_model_switch_reattaches_and_stop_removes_all_callbacks
    previous = @model
    previous_observer = previous.observers.first
    @model = Model.new
    @timer.tick
    assert_empty previous.observers
    assert_equal 1, @model.observers.length
    assert_equal [@model], @changes
    @watch.stop
    assert_empty @model.observers
    assert_equal [7], @timer.stopped
    previous_observer.onTransactionCommit(previous)
    @timer.tick
    assert_equal [@model], @changes, '規則：已關閉對話框不得再收到舊 watcher 回呼'
  end
end
