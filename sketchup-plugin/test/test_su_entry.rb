# frozen_string_literal: true

require 'minitest/autorun'
require 'json'
require 'open3'
require 'rbconfig'
require 'tmpdir'

class SketchUpEntryContractTest < Minitest::Test
  ENTRY = File.expand_path('../test_su/run_all.rb', __dir__)
  HARNESS = <<~'RUBY'
    require 'json'
    entry, output, count = ARGV
    ENV['GEOMETRY_FRAMING_SU_OUTPUT'] = output

    # 只隔離載入依賴，不取代 Runner、run、transaction 或 finish。
    # load 的仍是工作區實際驗收入口；除到達 start_operation 外不模擬幾何。
    $LOADED_FEATURES << 'sketchup.rb'
    $LOADED_FEATURES << File.expand_path('../geometry_framing/su/main.rb', File.dirname(entry))

    class ReachedFirstFixture < Exception; end

    class ContractEntities
      include Enumerable

      def initialize(count)
        @items = Array.new(count) { |index| "使用者實體#{index}" }.freeze
      end

      def each(&block)
        @items.each(&block)
      end

      def length
        @items.length
      end
      # 刻意沒有 empty?：Sketchup::Entities 官方 API 僅保證 length。
    end

    class ContractModel
      attr_reader :entities, :operations, :materials

      def initialize(count)
        @entities = ContractEntities.new(count)
        @operations = []
        @materials = {}.freeze # 真入口只讀取同名材質是否存在；不得改寫範本材質。
      end

      def active_path
        nil
      end

      def start_operation(name, disable_ui)
        @operations << [name, disable_ui]
        raise ReachedFirstFixture, '已到第一個夾具操作，停止在任何幾何寫入之前'
      end
    end

    module Sketchup
      class ModelObserver; end

      def self.active_model
        @model
      end

      def self.model=(model)
        @model = model
      end

      def self.version
        '26.0.0'
      end
    end

    model = ContractModel.new(Integer(count))
    Sketchup.model = model
    before = model.entities.to_a
    reached = false
    begin
      load entry
    rescue ReachedFirstFixture
      reached = true
    end
    result_path = File.join(output, 'result.json')
    result = File.exist?(result_path) ? JSON.parse(File.read(result_path, encoding: 'UTF-8')) : nil
    payload = { reached_fixture: reached, operations: model.operations,
                content_before: before, content_after: model.entities.to_a,
                entities_has_empty: model.entities.respond_to?(:empty?), report: result }
    puts("CONTRACT_RESULT=#{JSON.generate(payload)}")
  RUBY

  def exercise_entry(count)
    Dir.mktmpdir('geometry-framing-entry-contract') do |output|
      # 只供獨立突變驗證使用；正常與mutation runner都以各自副本的真入口為準。
      entry = ENV.fetch('GEOMETRY_FRAMING_TEST_ENTRY', ENTRY)
      stdout, status = Open3.capture2e(RbConfig.ruby, '-e', HARNESS, entry, output, count.to_s)
      assert status.success?, "B1 Entities API：入口契約子行程不得先因替身載入錯誤失敗\n#{stdout}"
      line = stdout.lines.find { |item| item.start_with?('CONTRACT_RESULT=') }
      refute_nil line, "B1 Entities API：真入口須留下可判讀結果\n#{stdout}"
      JSON.parse(line.delete_prefix('CONTRACT_RESULT='))
    end
  end

  def test_b1_empty_model_reaches_first_fixture_transaction_without_entities_empty
    result = exercise_entry(0)
    refute result.fetch('entities_has_empty'), 'B1 Entities API：替身不可偷補未提供的 empty?'
    assert result.fetch('reached_fixture'),
           "B1 Entities API：空白模型必須進入第一個夾具操作，不能因 Entities.empty? 提早失敗；實際#{result['report'].inspect}"
    assert_equal [['驗收夾具 平釘', true]], result.fetch('operations'), 'B1 Entities API：必須真的呼叫入口的第一個 transaction'
    assert_equal [], result.fetch('content_after'), 'B1 Entities API：sentinel 必須在任何幾何寫入之前停止'
    assert_nil result['report'], 'B1 Entities API：到達sentinel不是Runner失敗，不能由rescue假裝通過'
  end

  def test_b1_nonempty_model_is_rejected_without_touching_user_content
    result = exercise_entry(2)
    refute result.fetch('reached_fixture'), 'B1 Entities API：非空白模型不得開始建立夾具'
    assert_equal [], result.fetch('operations'), 'B1 Entities API：非空白模型不得呼叫start_operation'
    assert_equal result.fetch('content_before'), result.fetch('content_after'), 'B1 Entities API：使用者實體必須逐項保持不變'
    report = result.fetch('report')
    assert_equal false, report.fetch('passed'), 'B1 Entities API：拒絕非空白模型必須明確回報失敗'
    assert_equal 1, report.fetch('exit_code'), 'B1 Entities API：拒絕結果exit_code須為1'
    assert report.fetch('log').any? { |line| line.include?('請先開一個新的空白模型') },
           "B1 Entities API：非空白模型須因保護使用者內容而拒絕，不能是未定義API錯誤；實際#{report.inspect}"
  end
end
