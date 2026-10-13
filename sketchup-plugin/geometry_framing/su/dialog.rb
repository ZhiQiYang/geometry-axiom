# frozen_string_literal: true

require 'json'

module GeometryFraming
  module SU
    module Dialog
      module_function

      def show(mode = 'flat')
        @dialog.close if @dialog
        @mode = mode
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
      def evaluate(mode:, params: {}, model: Sketchup.active_model)
        snapshot = Selection.read(mode, model)
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

        evaluated = evaluate(mode: mode, params: params)
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
        warn("下角材：#{error.class}: #{error.message}\n#{error.backtrace&.first(5)&.join("\n")}")
        receive(mode: mode || @mode, ok: false, message: error.message,
                checks: [{ id: 'SU_INPUT', ok: false, title: '選取與模型輸入', detail: error.message }],
                counts: {}, params: {}, input: {})
      end

      def receive(payload)
        @dialog&.execute_script("window.GeometryFramingUI.receive(#{JSON.generate(payload)})")
      end
    end
  end
end
