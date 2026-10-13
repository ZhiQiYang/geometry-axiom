# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../geometry_framing/su/dialog'

class DialogLifecycleTest < Minitest::Test
  class FakeDialog
    STYLE_DIALOG = 0
    attr_reader :scripts
    class << self
      attr_accessor :instances
    end

    def initialize(_options)
      @scripts = []
      (self.class.instances ||= []) << self
    end

    def set_file(_path); end
    def add_action_callback(_name, &_block); end
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
end
