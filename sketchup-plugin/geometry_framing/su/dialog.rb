# frozen_string_literal: true

require 'json'

module GeometryFraming
  module SU
    module Dialog
      module_function

      def show(mode = 'flat')
        @dialog.close if @dialog
        @mode = mode
        @profile_choice = nil
        @dialog = UI::HtmlDialog.new(
          dialog_title: '下角材', preferences_key: 'GeometryFraming.Dialog', scrollable: true,
          resizable: true, width: 760, height: 780, min_width: 420, min_height: 440,
          style: UI::HtmlDialog::STYLE_DIALOG
        )
        @dialog.set_file(File.expand_path('../ui/dialog.html', __dir__))
        @dialog.add_action_callback('ready') { |_context| receive(initial_payload) }
        @dialog.add_action_callback('preview') { |_context, payload| dispatch(payload, false) }
        @dialog.add_action_callback('generate') { |_context, payload| dispatch(payload, true) }
        @dialog.set_on_closed { @dialog = nil }
        @dialog.show
      end

      def initial_payload
        { mode: @mode, ok: false, message: '選好天花面或正交折線後，按「檢查選取」。所有規則通過後才能建立。',
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
        { snapshot: snapshot, result: result }
      end

      def dispatch(raw, generate)
        payload = raw.is_a?(String) ? JSON.parse(raw) : raw
        raise InputError, '對話框參數必須是物件。' unless payload.is_a?(Hash)

        mode = payload['mode'] || @mode
        params = payload['params'] || {}
        raise InputError, '參數必須是物件。' unless params.is_a?(Hash)

        model = Sketchup.active_model
        start_vertex_id = nil
        chooser = nil
        if mode == 'profile'
          signature = selection_signature(model)
          @profile_choice = nil if @profile_choice && @profile_choice[:signature] != signature
          start_vertex_id = @profile_choice && @profile_choice[:id]
          if generate && start_vertex_id.nil?
            raise StartPointError, '選取已改變或尚未指定起點，請先重新檢查並選擇斷面起點。'
          end
          unless generate
            chooser = lambda do |choices|
              chosen = choose_profile_start(choices)
              @profile_choice = { signature: signature, id: chosen } if chosen
              chosen
            end
          end
        end
        evaluated = evaluate(mode: mode, params: params, model: model, start_vertex_id: start_vertex_id, &chooser)
        result, snapshot = evaluated.values_at(:result, :snapshot)
        ok = result[:checks].all? { |check| check[:ok] } && result[:valid] != false
        group = nil
        if generate && ok
          group = Builder.generate(mode: mode, result: result, frame: snapshot[:frame], input: snapshot[:input])
        end
        counts = result.fetch(:solids).group_by { |solid| solid[:role] }.transform_values(&:length)
        message = if group
                    "已建立「#{group.name}」，可用一次復原移除本次產生的全部構件。"
                  elsif ok
                    '所有檢查通過，可建立構件。'
                  else
                    '有規則未通過，請依下方原因調整；尚未建立任何構件。'
                  end
        receive(mode: mode, ok: ok, message: message, checks: result[:checks], counts: counts,
                params: result[:params] || params, input: snapshot[:input], generated: !group.nil?,
                suggested_ceil: result[:suggested_ceil])
      rescue StandardError => error
        @profile_choice = nil if error.is_a?(StartPointError)
        warn("下角材：#{error.class}: #{error.message}\n#{error.backtrace&.first(5)&.join("\n")}")
        receive(mode: mode || @mode, ok: false, message: error.message,
                checks: [{ id: 'SU_INPUT', ok: false, title: '選取與模型輸入', detail: error.message }],
                counts: {}, params: {}, input: {})
      end

      def selection_signature(model)
        [model.object_id, (model.active_path || []).map(&:persistent_id), model.selection.map(&:persistent_id).sort]
      end

      # 此選擇是一次性的原生對話框；不增加 HtmlDialog 常駐入口。
      # 無預選端點，按取消或未選擇都不會建立構件。
      def choose_profile_start(choices)
        choices = choices.sort_by { |choice| choice[:point] }
        labels = choices.each_with_index.map do |choice, index|
          coordinates = choice[:point].map { |value| format('%.3f', value) }.join(', ')
          "端點 #{index + 1}：世界 (#{coordinates}) mm"
        end
        prompt = '起點（會決定面材轉角搭接；請明示選擇）'
        answer = UI.inputbox([prompt], ['請選擇'], [(['請選擇'] + labels).join('|')], '下角材：指定斷面起點')
        return nil unless answer

        index = labels.index(answer.first)
        index ? choices[index][:id] : nil
      end

      def receive(payload)
        @dialog&.execute_script("window.GeometryFramingUI.receive(#{JSON.generate(payload)})")
      end
    end
  end
end
