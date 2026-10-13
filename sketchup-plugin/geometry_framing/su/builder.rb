# frozen_string_literal: true

require 'json'

module GeometryFraming
  module SU
    # 只將 core 已確認的軸向 boxes 寫入模型，不在此重算工法。
    module Builder
      DICTIONARY = 'GeometryFraming'
      ROLES = { 'board' => '面材', 'wall' => '沿邊料', 'pri' => '主支', 'sec' => '副支',
                'long' => '縱向料', 'rib' => '橫撐' }.freeze
      COLORS = { 'board' => '#DCCCA8', 'wall' => '#A57743', 'pri' => '#C34F3E',
                 'sec' => '#5989B4', 'long' => '#85502E', 'rib' => '#DC9A41' }.freeze
      module_function

      def generate(mode:, result:, frame:, input:, model: Sketchup.active_model)
        checks = result.fetch(:checks)
        unless checks.all? { |check| check[:ok] } && result[:valid] != false
          failed = checks.reject { |check| check[:ok] }.map { |check| "#{check[:id]}：#{check[:title]}" }
          raise InputError, "規則未通過，未建立任何構件。\n#{failed.join("\n")}"
        end

        solids = result.fetch(:solids)
        raise InputError, '核心沒有可建立的構件。' if solids.empty?

        solids.each { |solid| validate_solid!(solid) }
        group = nil
        Context.at_root(model) do
          started = false
          begin
            model.start_operation(mode == 'flat' ? '下角材 平釘' : '下角材 斷面', true)
            started = true
            group = model.entities.add_group
            group.name = "下角材 #{mode == 'flat' ? '平釘' : '斷面'} #{Time.now.strftime('%Y%m%d %H%M%S')}"
            group.layer = model.layers[0]
            group.transformation = frame
            group.set_attribute(DICTIONARY, 'mode', mode)
            group.set_attribute(DICTIONARY, 'version', GeometryFraming.const_defined?(:VERSION) ? GeometryFraming::VERSION : '0.1.0')
            group.set_attribute(DICTIONARY, 'unit', 'mm')
            group.set_attribute(DICTIONARY, 'params', JSON.generate(result[:params] || {}))
            group.set_attribute(DICTIONARY, 'input', JSON.generate(input))
            roles = {}
            solids.each do |solid|
              role = solid.fetch(:role).to_s
              roles[role] ||= make_role_group(model, group, role)
              definition = model.definitions.add("下角材 #{solid.fetch(:id)}")
              add_boxes(definition.entities, solid.fetch(:boxes), model.layers[0])
              instance = roles[role].entities.add_instance(definition, Geom::Transformation.new)
              instance.name = "#{ROLES.fetch(role)} #{solid.fetch(:id)}"
              instance.layer = roles[role].layer
              instance.material = material(model, role)
              attributes = { 'id' => solid.fetch(:id).to_s, 'role' => role, '角色' => ROLES.fetch(role),
                             'section_mm' => solid.fetch(:section), 'length_mm' => solid.fetch(:length),
                             'rule' => solid.fetch(:rule).to_s, '斷面' => solid.fetch(:section).join(' × ') + ' mm',
                             '長度' => solid.fetch(:length), '規則' => solid.fetch(:rule).to_s, 'unit' => 'mm' }
              attributes.each { |key, value| instance.set_attribute(DICTIONARY, key, value) }
            end
            model.commit_operation
            started = false
          rescue StandardError
            model.abort_operation if started
            raise
          end
        end
        group
      end

      def validate_solid!(solid)
        raise InputError, "未知構件角色：#{solid[:role]}" unless ROLES.key?(solid[:role].to_s)

        boxes = solid.fetch(:boxes)
        raise InputError, "構件 #{solid[:id]} 沒有幾何。" if boxes.empty?

        boxes.each do |box|
          unless box.length == 6 && box.all? { |value| value.is_a?(Numeric) && value.finite? } &&
                 (0..2).all? { |axis| box[axis + 3] > box[axis] }
            raise InputError, "構件 #{solid[:id]} 含無效 box，未建立模型。"
          end
        end
      end

      def make_role_group(model, parent, role)
        group = parent.entities.add_group
        group.name = ROLES.fetch(role)
        group.layer = model.layers.add("下角材 #{ROLES.fetch(role)}")
        group.set_attribute(DICTIONARY, 'role', role)
        group
      end

      def material(model, role)
        name = "下角材 #{ROLES.fetch(role)}"
        value = model.materials[name] || model.materials.add(name)
        value.color = COLORS.fetch(role)
        value
      end

      # 對多盒裁切面材取聯集的外皮：不留下共用面的內部隔板。
      # 所有離散切點都由 core box 邊界提供，沒有工法規則。
      def add_boxes(entities, boxes, untagged)
        axes = (0..2).map { |axis| boxes.flat_map { |box| [box[axis], box[axis + 3]] }.uniq.sort }
        occupied = {}
        (0...(axes[0].length - 1)).each do |i|
          (0...(axes[1].length - 1)).each do |j|
            (0...(axes[2].length - 1)).each do |k|
              center = [i, j, k].each_with_index.map { |index, axis| (axes[axis][index] + axes[axis][index + 1]) / 2.0 }
              occupied[[i, j, k]] = boxes.any? do |box|
                (0..2).all? { |axis| center[axis] > box[axis] && center[axis] < box[axis + 3] }
              end
            end
          end
        end
        occupied.each do |(i, j, k), present|
          next unless present

          x0, x1 = axes[0][i, 2]
          y0, y1 = axes[1][j, 2]
          z0, z1 = axes[2][k, 2]
          faces = [
            [[i - 1, j, k], [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]]],
            [[i + 1, j, k], [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]]],
            [[i, j - 1, k], [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]]],
            [[i, j + 1, k], [[x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [x1, y1, z0]]],
            [[i, j, k - 1], [[x0, y0, z0], [x0, y1, z0], [x1, y1, z0], [x1, y0, z0]]],
            [[i, j, k + 1], [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]]]
          ]
          faces.each do |neighbor, coordinates|
            next if occupied[neighbor]

            points = coordinates.map { |point| Geom::Point3d.new(point.map(&:mm)) }
            face = entities.add_face(points)
            raise InputError, 'SketchUp 無法建立構件面，整個動作已取消。' unless face

            expected = (points[1] - points[0]).cross(points[2] - points[0])
            face.reverse! if face.normal.dot(expected).negative?
          end
        end
        entities.each { |entity| entity.layer = untagged if entity.respond_to?(:layer=) }
      end
    end
  end
end
