# frozen_string_literal: true

module GeometryFraming
  module SU
    # Observer 只記錄變更；UI 更新由 timer 執行，不在 SketchUp 交易回呼內改模型。
    # 生成前另做完整 snapshot 比對，不能把延遲送達的 observer 當成安全閘門。
    class SelectionWatch
      EVENTS = %i[onActivePathChanged onTransactionCommit onTransactionUndo onTransactionRedo
                  onTransactionAbort onEraseAll onDeleteModel].freeze

      def self.signature(model)
        return nil unless model && (!model.respond_to?(:valid?) || model.valid?)

        path = (model.active_path || []).map do |entity|
          [entity.persistent_id, entity.respond_to?(:transformation) ? entity.transformation.to_a : nil]
        end
        selected = model.selection.map do |entity|
          vertices = entity.respond_to?(:vertices) ? entity.vertices.map do |vertex|
            [vertex.persistent_id, vertex.position.to_a.map(&:to_f)]
          end.sort_by(&:first) : []
          [entity.persistent_id, vertices]
        end.sort_by(&:first)
        [model.object_id, path, selected]
      end

      def initialize(model_provider:, timer_api:, &on_change)
        @model_provider, @timer_api, @on_change = model_provider, timer_api, on_change
        @stopped, @suspended, @dirty = false, false, false
        attach(@model_provider.call)
        @signature = self.class.signature(@model)
        @timer = @timer_api.start_timer(0.4, true) { tick }
      end

      def attach(model)
        detach
        @model = model
        return unless model && model.respond_to?(:add_observer) && defined?(Sketchup::ModelObserver)

        owner = self
        @observer = Class.new(Sketchup::ModelObserver) do
          SelectionWatch::EVENTS.each { |event| define_method(event) { |*_args| owner.changed(model) } }
        end.new
        @model.add_observer(@observer)
      end

      def detach
        @model.remove_observer(@observer) if @model && @observer && @model.respond_to?(:remove_observer)
      rescue StandardError
        # 已關閉的模型可能拒絕 remove_observer；stopped 仍使舊回呼失效。
        nil
      ensure
        @observer = nil
      end

      def changed(model = @model)
        @dirty = true if !@stopped && !@suspended && @model.equal?(model)
      end

      def tick
        return if @stopped || @suspended

        model = @model_provider.call
        if !@model.equal?(model)
          attach(model)
          @dirty = true
        end
        signature = self.class.signature(model)
        changed = @dirty || signature != @signature
        @dirty, @signature = false, signature
        @on_change.call(model) if changed
      rescue StandardError
        @on_change.call(nil) unless @stopped
      end

      def suspend
        previous = @suspended
        @suspended = true
        yield
      ensure
        @suspended = previous
        unless @stopped || @suspended
          @signature = begin
            self.class.signature(@model_provider.call)
          rescue StandardError
            nil
          end
          @dirty = false
        end
      end

      def stop
        @stopped = true
        @timer_api.stop_timer(@timer) if @timer
        @timer = nil
        detach
      end
    end
  end
end
