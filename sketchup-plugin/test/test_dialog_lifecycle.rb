# frozen_string_literal: true

require 'minitest/autorun'
require 'minitest/mock'
require_relative '../geometry_framing/su/dialog'

class DialogLifecycleTest < Minitest::Test
  class FakeDialog
    STYLE_DIALOG = 0
    attr_reader :scripts, :callbacks
    class << self
      attr_accessor :instances
    end

    def initialize(_options)
      @scripts = []
      @callbacks = {}
      (self.class.instances ||= []) << self
    end

    def set_file(_path); end
    def add_action_callback(name, &block) = @callbacks[name] = block
    def show; end
    def close; end # Deliberately deliver on_closed after the next dialog opens.
    def set_on_closed(&callback) = @on_closed = callback
    def fire_closed = @on_closed.call
    def execute_script(script) = @scripts << script
  end

  def setup
    @had_ui = Object.const_defined?(:UI, false)
    @old_ui = Object.const_get(:UI) if @had_ui
    Object.send(:remove_const, :UI) if @had_ui
    ui = Module.new
    ui.const_set(:HtmlDialog, FakeDialog)
    Object.const_set(:UI, ui)
    FakeDialog.instances = []
    @dialog = GeometryFraming::SU::Dialog
    @saved = @dialog.instance_variables.to_h { |key| [key, @dialog.instance_variable_get(key)] }
    @dialog.instance_variable_set(:@dialog, nil)
  end

  def teardown
    @dialog.instance_variables.each { |key| @dialog.remove_instance_variable(key) }
    @saved.each { |key, value| @dialog.instance_variable_set(key, value) }
    Object.send(:remove_const, :UI)
    Object.const_set(:UI, @old_ui) if @had_ui
  end

  def test_delayed_close_preserves_the_current_dialog
    @dialog.show('flat')
    previous = FakeDialog.instances.last
    @dialog.show('profile')
    current = FakeDialog.instances.last
    previous.fire_closed
    @dialog.receive(ok: true, message: '仍可收到結果')
    assert_equal 1, current.scripts.length, '規則：對話框生命週期，舊 close 回呼不得清除新對話框'
    current.fire_closed
    @dialog.receive(ok: true, message: '關閉後不再傳送')
    assert_equal 1, current.scripts.length, '規則：對話框生命週期，目前對話框關閉後不可再傳送'
  end

  def test_delayed_close_stops_its_own_watcher_without_detaching_the_new_one
    had_sketchup = Object.const_defined?(:Sketchup, false)
    Object.const_set(:Sketchup, Module.new) unless had_sketchup
    UI.define_singleton_method(:start_timer) { |*_args| }
    watchers = []
    factory = lambda do |**_args|
      watcher = Object.new
      watcher.define_singleton_method(:stop) { @stops = (@stops || 0) + 1 }
      watcher.define_singleton_method(:stops) { @stops || 0 }
      watchers << watcher
      watcher
    end
    GeometryFraming::SU::SelectionWatch.stub(:new, factory) do
      @dialog.show('flat')
      previous = FakeDialog.instances.last
      @dialog.show('profile')
      current = FakeDialog.instances.last
      assert_equal 1, watchers.first.stops, '規則：重開前停止前一個 watcher'
      previous.fire_closed
      assert_same watchers.last, @dialog.instance_variable_get(:@watch)
      assert_equal 0, watchers.last.stops, '規則：舊 close 不得停止新 watcher'
      current.fire_closed
      assert_equal 1, watchers.last.stops, '規則：目前對話框關閉時停止 watcher'
      assert_nil @dialog.instance_variable_get(:@watch)
    end
  ensure
    UI.singleton_class.send(:remove_method, :start_timer)
    Object.send(:remove_const, :Sketchup) unless had_sketchup
  end

  def test_old_dialog_action_callbacks_cannot_touch_the_new_dialog
    @dialog.show('flat')
    previous = FakeDialog.instances.last
    @dialog.show('profile')
    current = FakeDialog.instances.last
    @dialog.stub(:dispatch, ->(*) { flunk '舊 dialog callback 不得執行 preview 或 generate' }) do
      previous.callbacks.fetch('ready').call(nil)
      previous.callbacks.fetch('preview').call(nil, '{}')
      previous.callbacks.fetch('generate').call(nil, '{}')
    end
    assert_empty current.scripts, '規則：舊視窗的 ready／preview／generate 回呼不得污染新視窗'
    current.callbacks.fetch('ready').call(nil)
    assert_equal 1, current.scripts.length
  end
end
