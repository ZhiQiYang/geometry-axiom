# frozen_string_literal: true

# 輕量真機回歸：只由驗收者在 SketchUp 2026 的新空白模型 load。
# 不開 HtmlDialog、不呼叫原生起點選擇視窗、不用 send_action 或 UI timer。
require 'sketchup.rb'
require 'json'
require 'fileutils'
require_relative '../geometry_framing/su/main'

module GeometryFraming
  module Acceptance
    class WorkflowRunner
      PROFILE_POINTS = [[467, 0], [467, 148], [743, 148], [743, 351], [0, 351]].freeze

      def initialize
        @model = Sketchup.active_model
        @log = []
        @out = ENV['GEOMETRY_FRAMING_WORKFLOW_OUTPUT'] ||
               File.join(Sketchup.temp_dir, "geometry-framing-workflow-#{Time.now.strftime('%Y%m%d-%H%M%S')}")
        FileUtils.mkdir_p(@out)
      end

      def run
        raise '請另開新的空白模型；回歸腳本不會清除既有實體。' unless @model.entities.length.zero? && @model.active_path.nil?
        raise '本驗收目標是 SketchUp 2026。' unless Sketchup.version.to_i == 26

        record("開始工作流回歸 SketchUp #{Sketchup.version} / Ruby #{RUBY_VERSION}")
        make_flat_inputs
        preview_does_not_add_undo_step
        generation_undo_removes_only_latest_batch
        failed_generation_rolls_back_current_batch
        selection_and_parameter_gates
        profile_start_can_be_chosen_again
        finish
      rescue StandardError => error
        finish(error)
      end

      def record(message)
        @log << message
        puts(message)
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

      def select(*items)
        @model.selection.clear
        @model.selection.add(items.flatten)
      end

      def make_flat_inputs
        transaction('回歸夾具 群組內 A 與 B') do
          @input_group = @model.entities.add_group
          @input_group.name = '工作流回歸 輸入群組'
          @face_a = rectangle(@input_group.entities, 0)
          @face_b = rectangle(@input_group.entities, 3500)
        end
        @path = [@input_group]
        @model.active_path = @path
        select(@face_a)
      end

      def rectangle(entities, offset)
        points = [[offset, 0, 2500], [offset + 1200, 0, 2500],
                  [offset + 1200, -1200, 2500], [offset, -1200, 2500]]
        entities.add_face(points.map { |point| point.map(&:mm) })
      end

      def request(mode, params, generate: false, &choose_start)
        payload = SU::Dialog.dispatch({ 'mode' => mode, 'params' => params }, generate, model: @model, &choose_start)
        assert(payload.is_a?(Hash), 'SU_WORKFLOW_PAYLOAD：真實 Dialog.dispatch 必須回傳可判讀狀態')
        payload
      end

      def valid_preview(mode, params, &choose_start)
        payload = request(mode, params, &choose_start)
        assert(payload[:ok] && payload[:status].to_s == 'reviewed',
               "SU_WORKFLOW_PREVIEW：#{mode} 必須通過本次選取檢查，實際 #{payload.inspect}")
        payload
      end

      def generated_groups
        @model.entities.grep(Sketchup::Group).select do |group|
          %w[flat profile].include?(group.get_attribute(SU::Builder::DICTIONARY, 'mode'))
        end
      end

      def create_from_review(mode, params)
        before = generated_groups
        payload = request(mode, params, generate: true)
        added = generated_groups - before
        assert(payload[:generated] && added.length == 1,
               "SU_WORKFLOW_GENERATE：通過有效預覽後只建立一批，實際 #{payload.inspect}")
        added.first
      end

      def same_input_context(face, rule, after_native_undo: false)
        assert(@model.active_path == @path && face.valid?, "#{rule}：保留群組編輯路徑及原始輸入面")
        if after_native_undo
          record("INFO #{rule}：原生 Undo 後選取數量 #{@model.selection.length}；不要求 SketchUp 自動恢復選取")
        else
          assert(@model.selection.to_a == [face], "#{rule}：操作後保留目前選取")
        end
      end

      def preview_does_not_add_undo_step
        marker = nil
        transaction('回歸夾具 Undo 標記') { marker = @input_group.entities.add_cpoint([2500.mm, -2000.mm, 500.mm]) }
        select(@face_a)
        valid_preview('flat', {})
        same_input_context(@face_a, 'SU_PREVIEW_UNDO')
        assert(marker.valid?, 'SU_PREVIEW_UNDO：檢查本身不可更動 Undo 標記')
        # 只呼叫一次真正的 SketchUp undo；不以 mock 或自動多次復原掩蓋多餘交易。
        Sketchup.undo
        assert(!marker.valid?, 'SU_PREVIEW_UNDO：群組內預覽不增加 Undo 層，一次復原必須移除原先標記')
        assert(@face_a.valid? && @face_b.valid? && @input_group.valid?, 'SU_PREVIEW_UNDO：輸入夾具保留')
        same_input_context(@face_a, 'SU_PREVIEW_UNDO_AFTER', after_native_undo: true)
        select(@face_a)
      end

      def generation_undo_removes_only_latest_batch
        params_a = { 'corner' => 'tl' }
        valid_preview('flat', params_a)
        @batch_a = create_from_review('flat', params_a)
        same_input_context(@face_a, 'SU_BATCH_A_CONTEXT')
        params_b = { 'corner' => 'br' }
        valid_preview('flat', params_b)
        batch_b = create_from_review('flat', params_b)
        same_input_context(@face_a, 'SU_BATCH_B_CONTEXT')
        assert(@batch_a.valid? && batch_b.valid?, 'SU_BATCH_UNDO：A 與 B 兩批實際產物同時存在')
        Sketchup.undo
        assert(!batch_b.valid?, 'SU_BATCH_UNDO：只呼叫一次 Sketchup.undo，最新 B 批全部消失')
        assert(@batch_a.valid? && @face_a.valid? && @input_group.valid?, 'SU_BATCH_UNDO：前一 A 批與輸入群組必須保留')
        assert(generated_groups == [@batch_a], 'SU_BATCH_UNDO：模型中只剩前一批，不能留下新批部分角色')
        same_input_context(@face_a, 'SU_BATCH_UNDO_CONTEXT', after_native_undo: true)
        select(@face_a)
      end

      def rejected_without_geometry(params, rule)
        before = generated_groups.map(&:persistent_id)
        payload = request('flat', params, generate: true)
        assert(!payload[:ok] && !payload[:generated] && payload[:status].to_s == 'stale',
               "#{rule}：未重新檢查必須回報過期並拒絕建立，實際 #{payload.inspect}")
        assert(generated_groups.map(&:persistent_id) == before, "#{rule}：拒絕過期結果不得新增或刪除批次")
      end

      def model_inventory
        { roots: @model.entities.map(&:persistent_id).sort,
          definitions: @model.definitions.map(&:name).sort,
          materials: @model.materials.map(&:name).sort,
          layers: @model.layers.map(&:name).sort }
      end

      def failed_generation_rolls_back_current_batch
        params = { 'corner' => 'tr' }
        valid_preview('flat', params)
        before = model_inventory
        original = SU::Builder.method(:add_boxes)
        calls = 0
        SU::Builder.singleton_class.send(:define_method, :add_boxes) do |*args|
          calls += 1
          raise 'SU_ROLLBACK_INJECTED：第一件已完成後故意讓第二件建立失敗' if calls == 2

          original.call(*args)
        end
        begin
          payload = request('flat', params, generate: true)
        ensure
          SU::Builder.singleton_class.send(:define_method, :add_boxes, original)
        end
        assert(calls == 2, 'SU_ROLLBACK：必須真正完成第一件幾何後，才在第二件注入失敗')
        assert(payload[:status].to_s == 'error' && !payload[:generated] && !payload[:ok],
               "SU_ROLLBACK：當批中途失敗必須回報 error，實際 #{payload.inspect}")
        assert(@batch_a.valid? && @input_group.valid? && @face_a.valid? && @face_b.valid?,
               'SU_ROLLBACK：失敗後前一批、輸入群組及兩個原始面保留')
        assert(generated_groups == [@batch_a], 'SU_ROLLBACK：不可留下失敗當批的任何角色群組')
        after = model_inventory
        before.each do |kind, values|
          assert(after[kind] == values,
                 "SU_ROLLBACK_INVENTORY：#{kind} 的數量及名稱／ID 必須完整恢復；before=#{values.inspect} after=#{after[kind].inspect}")
        end
        same_input_context(@face_a, 'SU_ROLLBACK_CONTEXT')
      end

      def selection_and_parameter_gates
        params = { 'cap' => 450 }
        select(@face_a)
        valid_preview('flat', params)
        select(@face_b)
        rejected_without_geometry(params, 'SU_SELECTION_STALE')
        same_input_context(@face_b, 'SU_SELECTION_STALE_CONTEXT')
        valid_preview('flat', params)
        changed = { 'cap' => 300 }
        rejected_without_geometry(changed, 'SU_PARAMS_STALE')
        fresh = valid_preview('flat', changed)
        assert(fresh[:params][:cap] == 300, 'SU_PARAMS_REVIEW：重新檢查必須使用使用者變更的 cap')
        newest = create_from_review('flat', changed)
        assert(@batch_a.valid? && newest.valid?, 'SU_SELECTION_REVIEW：重新檢查 B 後可建立新批，前批仍保留')
        Sketchup.undo
        assert(!newest.valid? && @batch_a.valid?, 'SU_SELECTION_REVIEW_UNDO：B 重新檢查產物也只需一次復原')
      end

      def make_profile_inputs
        @model.active_path = nil
        edges = nil
        transaction('回歸夾具 明示斷面起點') do
          base = 10_000
          slab = @model.entities.add_group
          slab.name = '工作流回歸 RC 樓板'
          slab.entities.add_face([[-100, -100], [900, -100], [900, 1300], [-100, 1300]].map { |x, y| [(base + x).mm, y.mm, 2800.mm] })
          wall = @model.entities.add_group
          wall.name = '工作流回歸 RC 牆'
          wall.entities.add_face([[-100, 2300], [1300, 2300], [1300, 2900], [-100, 2900]].map { |y, z| [base.mm, y.mm, z.mm] })
          points = PROFILE_POINTS.map { |u, v| Geom::Point3d.new((base + u).mm, 0, (2800 - v).mm) }
          edges = @model.entities.add_edges(points)
          vertices = edges.flat_map(&:vertices).uniq
          @profile_start = vertices.find { |vertex| vertex.position == points.first }
          @profile_end = vertices.find { |vertex| vertex.position == points.last }
        end
        select(edges)
        edges
      end

      def profile_start_can_be_chosen_again
        edges = make_profile_inputs
        assert(@profile_start && @profile_end, 'SU_PROFILE_RESELECT：夾具有兩個明確端點')
        params = { 'L' => 1200, 'cap' => 300, 't' => 6, 'a' => 27, 'b' => 33 }
        choices_seen = []
        first = valid_preview('profile', params) do |choices, previous_id|
          choices_seen << [choices.map { |choice| choice[:id] }, previous_id]
          @profile_start.persistent_id
        end
        assert(first[:input][:start_vertex_id] == @profile_start.persistent_id, 'SU_PROFILE_RESELECT：第一輪使用明示起點')
        second = valid_preview('profile', params) do |choices, previous_id|
          choices_seen << [choices.map { |choice| choice[:id] }, previous_id]
          @profile_end.persistent_id
        end
        assert(choices_seen.length == 2, 'SU_PROFILE_RESELECT：同一折線已通過後再次檢查仍會重新詢問起點')
        assert(choices_seen.last[0].sort == [@profile_start.persistent_id, @profile_end.persistent_id].sort,
               'SU_PROFILE_RESELECT：只提供同一折線的兩端，不猜方向')
        assert(second[:input][:start_vertex_id] == @profile_end.persistent_id, 'SU_PROFILE_RESELECT：已通過的斷面可改從另一端開始')
        params.each do |key, value|
          assert(second[:params][key.to_sym] == value, "SU_PROFILE_PARAMS：換起點後保留 #{key}=#{value}")
        end
        assert(first[:input][:points] == second[:input][:points].reverse, 'SU_PROFILE_RESELECT：核心輸入確實反向，不只是更新文字')
        assert(@model.selection.to_a.sort_by(&:persistent_id) == edges.sort_by(&:persistent_id), 'SU_PROFILE_RESELECT：選取折線保持不變')
      end

      def finish(error = nil)
        if error
          record("FAIL #{error.class}: #{error.message}")
          record(error.backtrace.join("\n")) if error.backtrace
        end
        report = { passed: error.nil?, exit_code: error ? 1 : 0, sketchup: Sketchup.version, ruby: RUBY_VERSION,
                   assertions: @log.count { |line| line.start_with?('PASS') }, log: @log }
        File.write(File.join(@out, 'result.json'), JSON.pretty_generate(report), encoding: 'UTF-8')
        File.write(File.join(@out, 'output.txt'), @log.join("\n") + "\nexit_code=#{report[:exit_code]}\n", encoding: 'UTF-8')
        puts("工作流回歸#{error ? '失敗' : '完成'}，exit_code=#{report[:exit_code]}，證據：#{@out}")
        report
      end
    end
  end
end

GeometryFraming::Acceptance::WorkflowRunner.new.run
