# frozen_string_literal: true

module GeometryFraming
  module SU
    # 保留容器包圍盒的既有障礙語義；不猜測四面牆／整棟容器的材料分類。
    module Obstacles
      module_function

      def collect(model, selected_path:, face:, inverse:, api: Sketchup, geometry: Geom)
        Collector.new(model, selected_path, face, inverse, api, geometry).collect
      end

      class Collector
        TOL = 0.0001

        def initialize(model, selected_path, face, inverse, api, geometry)
          @model, @selected_path, @face, @inverse = model, selected_path, face, inverse
          @api, @geometry = api, geometry
        end

        def collect
          walk(@model.entities, @geometry.const_get(:Transformation).new, [])
        end

        private

        def container?(entity)
          entity.is_a?(@api.const_get(:Group)) || entity.is_a?(@api.const_get(:ComponentInstance))
        end

        def entities_of(instance)
          instance.is_a?(@api.const_get(:Group)) ? instance.entities : instance.definition.entities
        end

        def walk(entities, transform, path)
          visited = {}
          entities.flat_map do |entity|
            next [] unless container?(entity) || entity.is_a?(@api.const_get(:Face))

            next_path = path + [entity]
            next [] unless eligible?(next_path)

            if container?(entity)
              if @selected_path.take(next_path.length) == next_path
                walk(entities_of(entity), transform * entity.transformation, next_path)
              else
                # 仍以容器為一筆保守障礙；但不能讓不參與判定的後代擴張其範圍。
                bounds = @geometry.const_get(:BoundingBox).new
                visible_bounds(entities_of(entity), entity.transformation, next_path, bounds)
                [bounds_record(entity, bounds, transform, next_path)]
              end
            elsif entity.is_a?(@api.const_get(:Face)) && !(path == @selected_path && entity == @face) && !visited[entity]
              connected = entity.all_connected
              connected.each { |part| visited[part] = true }
              bounds = @geometry.const_get(:BoundingBox).new
              connected.each do |part|
                next unless eligible?(path + [part]) && part.respond_to?(:vertices)

                part.vertices.each { |vertex| bounds.add(vertex.position) }
              end
              [bounds_record(entity, bounds, transform, path + [entity])]
            else
              []
            end
          end.compact
        end

        # Drawingelement#hidden? 與 Layer/LayerFolder#visible? 各自有獨立旗標。
        # 不採 Model#drawing_element_visible?：開啟「顯示隱藏」會改變它的答案，
        # P-076 要求的是排除 hidden 實體，不因畫面顯示選項重新納入。
        # https://ruby.sketchup.com/Sketchup/Drawingelement.html#hidden%3F-instance_method
        # https://ruby.sketchup.com/Sketchup/Layer.html#visible%3F-instance_method
        # https://ruby.sketchup.com/Sketchup/LayerFolder.html#folder-instance_method
        def eligible?(path)
          # MUTATION: obstacle_generated_filter — 自產物不得在同面重跑時變成樑。
          return false if path.any? { |entity| generated?(entity) }
          # MUTATION: obstacle_visibility_filter — hidden/Tag/父階層可見性均須生效。
          return false unless path.all? { |entity| visible?(entity) }

          true
        end

        def generated?(entity)
          container?(entity) && !entity.attribute_dictionary('GeometryFraming', false).nil?
        end

        def visible?(entity)
          return false if entity.hidden?

          layer = entity.layer
          return false unless layer.visible?

          folder = layer.folder
          while folder
            return false unless folder.visible?

            folder = folder.folder
          end
          true
        end

        def visible_bounds(entities, transform, path, bounds)
          entities.each do |entity|
            # 非 Drawingelement（例如曲線定義）沒有獨立可見幾何，不是 bounds 來源。
            next unless entity.respond_to?(:hidden?) && entity.respond_to?(:layer)

            next_path = path + [entity]
            next unless eligible?(next_path)

            if container?(entity)
              visible_bounds(entities_of(entity), transform * entity.transformation, next_path, bounds)
            elsif entity.respond_to?(:vertices)
              entity.vertices.each { |vertex| bounds.add(vertex.position.transform(transform)) }
            elsif entity.respond_to?(:bounds) && !entity.bounds.empty?
              (0..7).each { |index| bounds.add(entity.bounds.corner(index).transform(transform)) }
            end
          end
        end

        def bounds_record(entity, bounds, transform, path)
          return nil if bounds.empty?

          points = (0..7).map do |index|
            bounds.corner(index).transform(transform).transform(@inverse).to_a.map { |value| value.to_mm.round(6) }
          end
          minimum = (0..2).map { |axis| points.map { |point| point[axis] }.min }
          maximum = (0..2).map { |axis| points.map { |point| point[axis] }.max }
          return nil if (0..2).any? { |axis| maximum[axis] - minimum[axis] < TOL }

          labels = path.map do |part|
            name = part.respond_to?(:name) ? part.name : ''
            if name.empty? && part.respond_to?(:definition) && part.definition.respond_to?(:name)
              name = part.definition.name
            end
            name = '模型實體' if name.empty?
            "#{name} (##{part.persistent_id})"
          end
          # core 會逐字把 id 帶進碰撞診斷，保留所有祖先名稱與 PID 以便定位。
          { id: labels.join(' / '), min: minimum, max: maximum }
        end
      end
    end
  end
end
