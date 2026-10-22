# frozen_string_literal: true

require 'json'
require 'digest'
require_relative 'selection_watch'

module GeometryFraming
  module SU
    module Dialog
      module_function

      def show(mode = 'flat')
        @watch&.stop
        @dialog.close if @dialog
        @mode, @profile_choice, @review, @has_result = mode, nil, nil, false
        @dialog = UI::HtmlDialog.new(
          dialog_title: '下角材', preferences_key: 'GeometryFraming.Dialog', scrollable: true,
          resizable: true, width: 760, height: 780, min_width: 420, min_height: 440,
          style: UI::HtmlDialog::STYLE_DIALOG
        )
        dialog = @dialog
        dialog.set_file(File.expand_path('../ui/dialog.html', __dir__))
        dialog.add_action_callback('ready') { |_context| receive(initial_payload) if @dialog.equal?(dialog) }
        dialog.add_action_callback('preview') { |_context, payload| dispatch(payload, false) if @dialog.equal?(dialog) }
        dialog.add_action_callback('generate') { |_context, payload| dispatch(payload, true) if @dialog.equal?(dialog) }
        watch = if defined?(Sketchup) && UI.respond_to?(:start_timer)
                  SelectionWatch.new(model_provider: -> { Sketchup.active_model }, timer_api: UI) do |model|
                    invalidate_review(model: model) if @dialog.equal?(dialog)
                  end
                end
        @watch = watch
        dialog.set_on_closed do
          watch&.stop
          if @dialog.equal?(dialog)
            @dialog, @watch, @review, @has_result = nil, nil, nil, false
          end
        end
        @dialog.show
      end

      def initial_payload
        label = @mode == 'profile' ? '檢查／選起點' : '檢查選取'
        { mode: @mode, status: 'unreviewed', ok: false,
          message: "尚未檢查。選好天花面或正交折線後，按「#{label}」。所有規則通過後才能新增一批角材。",
          checks: [], counts: {}, params: {}, input: {} }
      end

      # test_su 可直接呼叫，不需模擬 HtmlDialog 事件。
      def evaluate(mode:, params: {}, model: Sketchup.active_model, start_vertex_id: nil, &choose_start)
        snapshot = Selection.read(mode, model, start_vertex_id: start_vertex_id, &choose_start)
        effective = params.transform_keys(&:to_sym)
        result = if mode == 'flat'
                   effective[:ceil] = snapshot[:input][:ceil] unless effective.key?(:ceil)
                   Core::FlatCeiling.build(rings: snapshot[:input][:rings], params: effective,
                                           obstacles: snapshot[:obstacles], id: "F#{snapshot[:input][:source_id]}")
                 else
                   Core::Profile.build(points: snapshot[:input][:points], params: effective)
                 end
        describe_selection(mode, model, snapshot, result)
        { snapshot: snapshot, result: result }
      end

      # 與原生驗收共用同一條 stale gate；注入 chooser 不會繞過起點或快照比對。
      def dispatch(raw, generate, model: Sketchup.active_model, &choose_start)
        @watch&.tick
        work = -> { perform_dispatch(raw, generate, model, &choose_start) }
        @watch ? @watch.suspend(&work) : work.call
      end

      def perform_dispatch(raw, generate, model, &choose_start)
        payload = raw.is_a?(String) ? JSON.parse(raw) : raw
        raise InputError, '對話框參數必須是物件。' unless payload.is_a?(Hash)

        mode = payload['mode'] || payload[:mode] || @mode
        @mode = mode
        params = payload['params'] || payload[:params] || {}
        raise InputError, '參數必須是物件。' unless params.is_a?(Hash)

        signature = selection_signature(model)
        if generate && (!@review || @review[:mode] != mode || @review[:selection] != signature)
          label = mode == 'profile' ? '檢查／選起點' : '檢查選取'
          return invalidate_review(model: model, message: "選取或模型已變更，或尚未完成檢查。請先按「#{label}」再新增。", force: true)
        end

        @review = nil unless generate
        start_vertex_id, chooser = nil, nil
        if mode == 'profile'
          @profile_choice = nil if @profile_choice && @profile_choice[:signature] != signature
          previous_id = @profile_choice && @profile_choice[:id]
          start_vertex_id = previous_id if generate
          unless generate
            chooser = lambda do |choices|
              chosen = choose_start ? choose_start.call(choices, previous_id) : choose_profile_start(choices, previous_id)
              @profile_choice = { signature: signature, id: chosen } if chosen
              chosen
            end
          end
        end

        evaluated = evaluate(mode: mode, params: params, model: model, start_vertex_id: start_vertex_id, &chooser)
        result, snapshot = evaluated.values_at(:result, :snapshot)
        ok = result[:checks].all? { |check| check[:ok] } && result[:valid] != false
        stamp = snapshot_stamp(snapshot, result)
        if selection_signature(model) != signature
          return invalidate_review(model: model, message: '檢查期間選取或模型已改變，請重新檢查。', force: true)
        end
        # 即使 observer 尚未送達，仍同步核對參數、幾何、變換與來源識別。
        if generate && @review[:stamp] != stamp
          return invalidate_review(model: model, message: '參數或模型幾何與上一輪檢查不同，請重新檢查後再新增。', force: true)
        end

        group = nil
        if generate && ok
          group = Builder.generate(mode: mode, result: result, frame: snapshot[:frame], input: snapshot[:input], model: model)
          @review = nil # 每次成功檢查只允許新增一批，避免重複點按。
        elsif ok
          @review = { mode: mode, selection: selection_signature(model), stamp: stamp }
        end
        counts = result.fetch(:solids).group_by { |solid| solid[:role] }.transform_values(&:length)
        @has_result = true
        message = if group
                    "已新增「#{group.name}」。既有批次仍保留；一次復原可移除本次新增的全部構件。再次新增前請重新檢查。"
                  elsif ok
                    '所有檢查通過，可以新增一批角材。'
                  else
                    '有規則未通過，請依下方原因調整；尚未建立任何構件。'
                  end
        receive(mode: mode, status: group ? 'generated' : 'reviewed', ok: ok && group.nil?, message: message,
                checks: result[:checks], counts: counts, params: result[:params] || params,
                input: snapshot[:input], generated: !group.nil?, suggested_ceil: result[:suggested_ceil])
      rescue StandardError => error
        @review = nil
        warn("下角材：#{error.class}: #{error.message}\n#{error.backtrace&.first(5)&.join("\n")}")
        receive(mode: mode || @mode, status: 'error', ok: false, message: error.message,
                preserve_result: true, generated: false,
                error_check: { id: 'SU_INPUT', ok: false, title: '選取與模型輸入', detail: error.message })
      end

      def invalidate_review(model: nil, message: '選取或模型已變更，請重新檢查。', force: false)
        # 已過期的結果仍顯示「目前選取」；後續變更必須繼續更新來源標示。
        # @review 是生成授權，@has_result 只表示畫面有一輪歷史結果。
        return unless @review || @has_result || force

        @review = nil
        receive(status: 'stale', ok: false, message: message, preserve_result: true,
                generated: false, selection_label: selection_label(model))
      end

      def selection_signature(model)
        SelectionWatch.signature(model)
      end

      def snapshot_stamp(snapshot, result)
        digest_value(input: snapshot[:input], frame: snapshot[:frame].to_a, obstacles: snapshot[:obstacles],
                     params: result[:params], checks: result[:checks], solids: result[:solids])
      end

      def digest_value(value)
        Digest::SHA256.hexdigest(JSON.generate(canonical(value)))
      end

      def canonical(value)
        case value
        when Hash then value.sort_by { |key, _| key.to_s }.map { |key, item| [key.to_s, canonical(item)] }
        when Array then value.map { |item| canonical(item) }
        when Float then value.finite? && value == value.to_i ? value.to_i : value
        else value
        end
      end

      def entity_label(entity)
        name = entity.respond_to?(:name) ? entity.name.to_s : ''
        name = entity.definition.name.to_s if name.empty? && entity.respond_to?(:definition)
        name.empty? ? "#{entity.typename} ##{entity.persistent_id}" : "#{name} ##{entity.persistent_id}"
      end

      def selection_label(model)
        return '尚未選取' unless model && !model.selection.empty?

        path = (model.active_path || []).map { |entity| entity_label(entity) }
        leaf = model.selection.length == 1 ? entity_label(model.selection.first) : "#{model.selection.length} 個實體"
        (path + [leaf]).join(' / ')
      end

      def describe_selection(mode, model, snapshot, result)
        input, frame = snapshot.values_at(:input, :frame)
        path = (model.active_path || []).map { |entity| entity_label(entity) }
        input[:source_name] = path.empty? ? input[:source] : "#{path.last} / #{input[:source]}"
        input[:source_path_names] = path
        input[:source_path_label] = path.empty? ? '模型根層' : path.join(' / ')
        origin = frame.origin.to_a.map { |value| value.to_mm.round(6) }
        x, y, z = [frame.xaxis, frame.yaxis, frame.zaxis].map { |axis| axis.to_a.map(&:to_f) }
        input[:origin_world_mm] = origin
        if mode == 'flat'
          points = input[:rings].flatten(1)
          minx, maxx = points.map(&:first).minmax
          miny, maxy = points.map(&:last).minmax
          input[:bounds_mm] = [minx, miny, maxx, maxy]
          input[:directions_world] = { x: x, y: y }
          input[:corner_map] = { tl: [minx, miny], tr: [maxx, miny], bl: [minx, maxy], br: [maxx, maxy] }.transform_values do |px, py|
            (0..2).map { |axis| (origin[axis] + x[axis] * px + y[axis] * py + z[axis] * input[:ceil]).round(6) }
          end
        else
          input[:directions_world] = { u: x, v: z.map { |value| -value }, L: y }
          last = input[:points].last
          input[:end_point_mm] = (0..2).map { |axis| (origin[axis] + x[axis] * last[0] - z[axis] * last[1]).round(6) }
          input[:profile_segments] = result[:segs]
          input[:profile_ring] = result[:ring]
          input[:profile_flip] = result[:params][:flip]
        end
      end

      # 每次明示檢查都可改選起點；沿用前次選擇作預設，不重開 HtmlDialog。
      def choose_profile_start(choices, previous_id = nil)
        choices = choices.sort_by { |choice| choice[:point] }
        labels = choices.each_with_index.map do |choice, index|
          coordinates = choice[:point].map { |value| format('%.3f', value) }.join(', ')
          "端點 #{index + 1}：世界 (#{coordinates}) mm"
        end
        previous_index = choices.index { |choice| choice[:id] == previous_id }
        selected = previous_index ? labels[previous_index] : '請選擇'
        prompt = '起點（決定面材轉角搭接，可重新選擇）'
        answer = UI.inputbox([prompt], [selected], [(['請選擇'] + labels).join('|')], '下角材：指定斷面起點')
        return nil unless answer

        index = labels.index(answer.first)
        index ? choices[index][:id] : nil
      end

      def receive(payload)
        @dialog&.execute_script("window.GeometryFramingUI.receive(#{JSON.generate(payload)})")
        payload
      end
    end
  end
end
