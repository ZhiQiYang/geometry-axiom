# frozen_string_literal: true

# 只由驗收者在 SketchUp 2026 Ruby Console 執行；本檔不會自行啟動 SketchUp。
# 先開新的空白模型，再 load 'D:/geometry-axiom/sketchup-plugin/test_su/run_all.rb'
# 若模型含任何實體便拒絕；不清空使用者模型。結果及截圖寫到系統暫存目錄。
require 'sketchup.rb'
require 'json'
require 'fileutils'
require_relative '../geometry_framing/su/main'

module GeometryFraming
  module Acceptance
    class UndoObserver < Sketchup::ModelObserver
      def initialize(&callback)
        @callback = callback
      end

      def onTransactionUndo(_model)
        @callback.call
      end
    end

    class Runner
      RINGS = [[[0, 0], [5000, 0], [5000, 3200], [3200, 3200], [3200, 4800], [0, 4800]],
               [[1200, 1200], [1600, 1200], [1600, 1600], [1200, 1600]]].freeze

      def initialize
        @model = Sketchup.active_model
        @log = []
        @out = ENV['GEOMETRY_FRAMING_SU_OUTPUT'] || File.join(Sketchup.temp_dir, "geometry-framing-su-#{Time.now.strftime('%Y%m%d-%H%M%S')}")
        FileUtils.mkdir_p(@out)
      end

      def run
        raise '請先開一個新的空白模型；驗收腳本不會刪除既有模型。' unless @model.entities.empty? && @model.active_path.nil?
        raise '本驗收目標是 SketchUp 2026。' unless Sketchup.version.to_i == 26

        record("開始 SketchUp #{Sketchup.version} / Ruby #{RUBY_VERSION} 驗收")
        transaction('驗收夾具 平釘') { @flat = ceiling(@model.entities) }
        select(@flat)
        evaluated = SU::Dialog.evaluate(mode: 'flat', model: @model)
        assert(evaluated[:result][:valid], 'SU_FLAT_CHECKS：L 形天花含 400 × 400 柱孔必須通過核心檢查')
        group = generate('flat', evaluated)
        verify_members(group, evaluated[:result], 'SU_FLAT')
        screenshot(group, 'flat.png')
        undo_once(group, 'SU_FLAT_UNDO') do
          assert(@flat.valid?, 'SU_FLAT_UNDO：一步復原必須保留輸入天花面')
          raw_obstacle
          profile
        end
      rescue StandardError => error
        finish(error)
      end

      def assert(condition, message)
        raise message unless condition

        record("PASS #{message}")
      end

      def transaction(name)
        @model.start_operation(name, true)
        yield
        @model.commit_operation
      rescue StandardError
        @model.abort_operation
        raise
      end

      def ceiling(entities)
        make = ->(ring) { ring.map { |x, y| Geom::Point3d.new(x.mm, -y.mm, 2500.mm) } }
        face = entities.add_face(make.call(RINGS[0]))
        hole = entities.add_face(make.call(RINGS[1]))
        hole.erase!
        # add_face 切孔之後重新取得有兩個圈的真正天花面。
        face = entities.grep(Sketchup::Face).find { |candidate| candidate.loops.length == 2 }
        raise 'SU_FIXTURE：無法建立 L 形含孔天花面' unless face

        face
      end

      def select(*entities)
        @model.selection.clear
        @model.selection.add(entities.flatten)
      end

      def generate(mode, evaluated)
        snapshot = evaluated[:snapshot]
        SU::Builder.generate(mode: mode, result: evaluated[:result], frame: snapshot[:frame], input: snapshot[:input], model: @model)
      end

      def verify_members(group, result, prefix)
        expected = result[:solids].group_by { |solid| solid[:role] }.transform_values(&:length)
        actual = {}
        group.entities.grep(Sketchup::Group).each do |role_group|
          role = role_group.get_attribute(SU::Builder::DICTIONARY, 'role')
          members = role_group.entities.grep(Sketchup::ComponentInstance)
          actual[role] = members.length
          members.each do |member|
            id = member.get_attribute(SU::Builder::DICTIONARY, 'id')
            source = result[:solids].find { |solid| solid[:id] == id }
            assert(!source.nil?, "#{prefix}_ID：#{id} 可回查核心")
            %w[role section_mm length_mm rule].each do |key|
              assert(!member.get_attribute(SU::Builder::DICTIONARY, key).nil?, "#{prefix}_ATTRIBUTE：#{id} 有 #{key}")
            end
            assert(member.layer == role_group.layer, "#{prefix}_TAG：#{id} 使用角色 Tag")
            assert(member.manifold?, "#{prefix}_SOLID：#{id} 為封閉實體，裁切盒沒有內隔板")
            assert(member.definition.entities.all? { |entity| !entity.respond_to?(:layer) || entity.layer == @model.layers[0] },
                   "#{prefix}_UNTAGGED：#{id} 原始幾何使用 Untagged")
          end
        end
        assert(actual == expected, "#{prefix}_COUNTS：角色數量 #{actual.inspect} 與 core #{expected.inspect} 一致")
        assert(group.parent == @model, "#{prefix}_TOP_LEVEL：結果是模型頂層群組")
      end

      def raw_obstacle
        before = @model.entities.to_a
        transaction('驗收夾具 未分組樑') do
          SU::Builder.add_boxes(@model.entities, [[2500, -2600, 2510, 2800, -2300, 2650]], @model.layers[0])
        end
        beam_entities = @model.entities.to_a - before
        select(@flat)
        evaluated = SU::Dialog.evaluate(mode: 'flat', model: @model)
        assert(!evaluated[:result][:valid], 'SU_RAW_BEAM：未分組樑的連通幾何 bounds 必須攔截碰撞')
        count = @model.entities.length
        begin
          generate('flat', evaluated)
          raise 'SU_CHECK_GATE：檢查失敗仍可建立構件'
        rescue SU::InputError
          assert(@model.entities.length == count, 'SU_CHECK_GATE：檢查失敗不得改模型')
        end
        transaction('驗收清除樑夾具') { @model.entities.erase_entities(beam_entities.select(&:valid?)) }
      end

      def profile
        edges = nil
        transaction('驗收夾具 斷面') do
          base = 10_000
          slab = @model.entities.add_group
          slab.name = '驗收 RC 樓板'
          slab.entities.add_face([[-200, -200], [1400, -200], [1400, 2700], [-200, 2700]].map { |x, y| [(base + x).mm, y.mm, 2800.mm] })
          wall = @model.entities.add_group
          wall.name = '驗收 RC 牆'
          wall.entities.add_face([[-200, 2200], [2700, 2200], [2700, 2900], [-200, 2900]].map { |y, z| [base.mm, y.mm, z.mm] })
          points = [[467, 0], [467, 148], [743, 148], [743, 351], [0, 351]].map { |u, v| [(base + u).mm, 0, (2800 - v).mm] }
          edges = @model.entities.add_edges(points)
        end
        select(edges)
        evaluated = SU::Dialog.evaluate(mode: 'profile', model: @model)
        assert(evaluated[:result][:valid], 'SU_PROFILE_CHECKS：間接照明槽七項檢查全通過')
        assert(evaluated[:result][:boards].length == 4 && evaluated[:result][:longs].length == 6 && evaluated[:result][:ribs].length == 4,
               'SU_PROFILE_SECTION：4 塊面材、6 支縱向料、每站 4 支橫撐')
        group = generate('profile', evaluated)
        verify_members(group, evaluated[:result], 'SU_PROFILE')
        screenshot(group, 'profile.png')
        undo_once(group, 'SU_PROFILE_UNDO') do
          assert(edges.all?(&:valid?), 'SU_PROFILE_UNDO：一步復原必須保留輸入折線與 RC')
          same_slab_profile
          nested_context
        end
      end

      def same_slab_profile
        edges = nil
        transaction('驗收夾具 同樓板斷面') do
          slab = @model.entities.add_group
          slab.entities.add_face([[20_000, -100, 2800], [21_000, -100, 2800], [21_000, 2700, 2800], [20_000, 2700, 2800]].map { |point| point.map(&:mm) })
          points = [[20_100, 0, 2800], [20_100, 0, 2500], [20_600, 0, 2500], [20_600, 0, 2800]].map { |point| point.map(&:mm) }
          edges = @model.entities.add_edges(points)
        end
        select(edges)
        evaluated = SU::Dialog.evaluate(mode: 'profile', model: @model)
        assert(evaluated[:result][:valid], 'SU_PROFILE_SAME_SLAB：兩端接同一樓板依 demo 直接封閉')
        reference = evaluated[:snapshot][:input][:reference]
        assert(reference[:slab] && !reference[:wall], 'SU_PROFILE_SAME_SLAB：不能虛構 RC 牆')
      end

      def nested_context
        outer = inner = face = nil
        transaction('驗收夾具 旋轉巢狀群組') do
          outer = @model.entities.add_group
          inner = outer.entities.add_group
          face = ceiling(inner.entities)
          origin = Geom::Point3d.new(30_000.mm, 20_000.mm, 0)
          outer.transformation = Geom::Transformation.translation(origin) * Geom::Transformation.rotation(ORIGIN, Z_AXIS, 1.degrees)
          inner.transformation = Geom::Transformation.translation([500.mm, 800.mm, 0])
        end
        @model.active_path = [outer, inner]
        select(face)
        path = @model.active_path.dup
        evaluated = SU::Dialog.evaluate(mode: 'flat', model: @model)
        assert(@model.active_path == path && @model.selection.to_a == [face], 'SU_CONTEXT_PREVIEW：預覽後保留巢狀編輯路徑與選取')
        assert(evaluated[:result][:valid], 'SU_CONTEXT_COORDINATES：旋轉平移後仍通過核心正交檢查')
        group = generate('flat', evaluated)
        assert(@model.active_path == path && @model.selection.to_a == [face], 'SU_CONTEXT_GENERATE：產生後保留巢狀編輯路徑與選取')
        assert(@model.entities.include?(group), 'SU_CONTEXT_ROOT：在巢狀群組內選面仍產生模型頂層結果')
        # 一個 core 板角點經輸出 frame 轉換，應位在選取天花的世界高度。
        box = evaluated[:result][:solids].find { |solid| solid[:role] == 'board' }[:boxes].first
        point = Geom::Point3d.new(box[0, 3].map(&:mm)).transform(group.transformation)
        assert((point.z.to_mm - 2500).abs < 0.001, 'SU_CONTEXT_HEIGHT：沒有重複套用編輯座標 transform')
        screenshot(group, 'nested-flat.png')
        undo_once(group, 'SU_CONTEXT_UNDO') do
          assert(face.valid? && outer.valid? && inner.valid?, 'SU_CONTEXT_UNDO：一次復原只移除結果，夾具仍在')
          assert(@model.active_path == path, 'SU_CONTEXT_UNDO：一步復原後仍在原編輯路徑')
          @model.active_path = nil
          finish
        end
      end

      def screenshot(group, name)
        view = @model.active_view
        center = group.bounds.center
        eye = center.offset(Geom::Vector3d.new(6000.mm, -7000.mm, 5000.mm))
        view.camera = Sketchup::Camera.new(eye, center, Geom::Vector3d.new(0, 0, 1))
        view.zoom(group)
        view.refresh
        path = File.join(@out, name)
        assert(view.write_image(filename: path, width: 1600, height: 1000, antialias: true), "SU_SCREENSHOT：#{path}")
      end

      # send_action 的 undo 是 UI 非同步動作。真正收到 onTransactionUndo
      # 後才驗證，不能用同步 Ruby 腳本錯把還沒執行的 undo 當成失敗。
      def undo_once(group, rule, &continuation)
        finished = false
        observer = UndoObserver.new do
          next if finished

          finished = true
          UI.start_timer(0, false) do
            begin
              @model.remove_observer(observer)
              assert(!group.valid?, "#{rule}：只發出一次 editUndo 就移除整個產物")
              continuation.call
            rescue StandardError => error
              finish(error)
            end
          end
        end
        @model.add_observer(observer)
        Sketchup.send_action('editUndo:')
        UI.start_timer(5, false) do
          next if finished

          finished = true
          @model.remove_observer(observer)
          finish(RuntimeError.new("#{rule}：5 秒內未收到復原事件"))
        end
      end

      def record(message)
        @log << message
        puts(message)
      end

      def finish(error = nil)
        return if @finished

        @finished = true
        if error
          record("FAIL #{error.class}: #{error.message}")
          record(error.backtrace.join("\n")) if error.backtrace
        end
        report = { passed: error.nil?, exit_code: error ? 1 : 0, sketchup: Sketchup.version,
                   ruby: RUBY_VERSION, assertions: @log.count { |line| line.start_with?('PASS') }, log: @log }
        File.write(File.join(@out, 'result.json'), JSON.pretty_generate(report), encoding: 'UTF-8')
        File.write(File.join(@out, 'output.txt'), @log.join("\n") + "\nexit_code=#{report[:exit_code]}\n", encoding: 'UTF-8')
        puts("SketchUp 驗收#{error ? '失敗' : '完成'}，exit_code=#{report[:exit_code]}，證據：#{@out}")
        # 不呼叫 Kernel.exit，避免把使用者的 SketchUp 關掉。
      end
    end
  end
end

GeometryFraming::Acceptance::Runner.new.run
