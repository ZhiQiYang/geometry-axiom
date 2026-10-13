# frozen_string_literal: true

module GeometryFraming
  module SU
    class InputError < StandardError; end
    class StartPointError < InputError; end

    # SketchUp 在開啟元件編輯時會改變幾何讀取的座標系。暫時關閉編輯，
    # 再讀定義座標與完整 instance path；離開時保全編輯路徑與原選取。
    # 不在 start_operation 內切換 context，避免把產生動作切成多個操作。
    module Context
      module_function

      def at_root(model)
        path = model.active_path
        selected = model.selection.to_a
        model.active_path = nil if path
        transform = (path || []).reduce(Geom::Transformation.new) { |t, instance| t * instance.transformation }
        yield(selected, path || [], transform)
      ensure
        if model && model.valid?
          model.active_path = path if path && path.all?(&:valid?)
          model.selection.clear
          model.selection.add(selected.select(&:valid?)) if selected
        end
      end
    end

    module Selection
      TOL = 0.0001 # mm；僅用於讀取 API 浮點座標，非放寬 demo 的規則。
      module_function

      def read(mode, model = Sketchup.active_model, start_vertex_id: nil, &choose_start)
        Context.at_root(model) do |selected, path, transform|
          case mode
          when 'flat' then flat(model, selected, path, transform)
          when 'profile' then profile(model, selected, path, transform, start_vertex_id: start_vertex_id, &choose_start)
          else raise InputError, '未知模式。請選平釘天花或斷面設計。'
          end
        end
      end

      def mm(value)
        value.to_mm.round(6)
      end

      def xyz(point)
        point.to_a.map { |value| mm(value) }
      end

      def dot(a, b)
        a.zip(b).sum { |x, y| x * y }
      end

      def sub(a, b)
        a.zip(b).map { |x, y| x - y }
      end

      def cross(a, b)
        [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
      end

      def normalize(vector)
        size = Math.sqrt(dot(vector, vector))
        raise InputError, '選取含有零長度方向，無法建立座標。' if size < TOL

        vector.map { |value| value / size }
      end

      def canonical_horizontal(vector)
        unit = normalize([vector[0], vector[1], 0.0])
        sign = unit[0].abs > 1.0e-8 ? unit[0] : unit[1]
        sign.negative? ? unit.map { |value| -value } : unit
      end

      def transform_for(origin_mm, xaxis, yaxis)
        Geom::Transformation.axes(
          Geom::Point3d.new(origin_mm.map(&:mm)),
          Geom::Vector3d.new(xaxis), Geom::Vector3d.new(yaxis), Geom::Vector3d.new(0, 0, 1)
        )
      end

      def flat(model, selected, path, transform)
        unless selected.length == 1 && selected.first.is_a?(Sketchup::Face)
          raise InputError, '平釘模式請只選一個水平、正交的天花完成面；柱孔須是該面的內圈。'
        end

        face = selected.first
        if face.all_connected.grep(Sketchup::Face).any? { |connected| connected != face }
          raise InputError, '完成面與其他未分組的面相連，無法分辨自身邊界與障礙樑。請先把完成面、樑等障礙分組後重試；相連實體的障礙分類待使用者決定。'
        end
        loops = [face.outer_loop] + face.loops.reject(&:outer?)
        world_rings = loops.map { |loop| loop.vertices.map { |vertex| xyz(vertex.position.transform(transform)) } }
        z = world_rings.first.first[2]
        unless world_rings.flatten(1).all? { |point| (point[2] - z).abs < TOL }
          raise InputError, '只接受世界座標中的水平面；斜面尚待使用者決定。'
        end

        directions = world_rings.first.each_with_index.map do |point, i|
          canonical_horizontal(sub(world_rings.first[(i + 1) % world_rings.first.length], point))
        end
        # 兩個正交軸之中，較接近模型紅軸的方向作為平面 X 正向。
        xaxis = directions.max_by { |direction| [direction[0].abs.round(8), direction[1].abs] }
        yaxis = [xaxis[1], -xaxis[0], 0.0] # demo 的 Y 朝平面圖下方。
        projected = world_rings.map { |ring| ring.map { |point| [dot(point, xaxis), dot(point, yaxis)] } }
        minx = projected.flatten(1).map(&:first).min
        miny = projected.flatten(1).map(&:last).min
        lengths = projected.map(&:length)
        snapped = snap_axes(projected.flatten(1).map { |x, y| [x - minx, y - miny] })
        rings = lengths.map { |length| snapped.shift(length) }
        rings.each do |ring|
          ring.each_with_index do |a, i|
            b = ring[(i + 1) % ring.length]
            unless (a[0] - b[0]).abs < TOL || (a[1] - b[1]).abs < TOL
              raise InputError, '外圈或柱孔有非正交邊；此情況 demo 未定義，待使用者決定。'
            end
          end
        end
        rings = rings.map { |ring| clean(ring, closed: true) }
        origin = xaxis.zip(yaxis).map { |x, y| x * minx + y * miny }
        frame = transform_for(origin, xaxis, yaxis)
        obstacles = obstacle_boxes(model.entities, Geom::Transformation.new, [], path, face, frame.inverse)
        {
          input: { rings: rings, ceil: z, source: "水平完成面 ##{face.persistent_id}",
                   axis_note: '平面 X 為較接近模型紅軸的正交邊方向；Y 朝其右側（圖下）。',
                   source_path: path.map(&:persistent_id), source_id: face.persistent_id },
          frame: frame, obstacles: obstacles
        }
      end

      def container?(entity)
        entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)
      end

      def entities_of(instance)
        instance.is_a?(Sketchup::Group) ? instance.entities : instance.definition.entities
      end

      def obstacle_boxes(entities, transform, path, selected_path, face, inverse)
        visited = {}
        entities.flat_map do |entity|
          if container?(entity)
            next_path = path + [entity]
            if selected_path.take(next_path.length) == next_path
              obstacle_boxes(entities_of(entity), transform * entity.transformation, next_path, selected_path, face, inverse)
            else
              [bounds_record(entity, entity.bounds, transform, inverse, next_path)]
            end
          elsif entity.is_a?(Sketchup::Face) && !(path == selected_path && entity == face) && !visited[entity]
            connected = entity.all_connected
            connected.each { |part| visited[part] = true }
            bounds = Geom::BoundingBox.new
            connected.grep(Sketchup::Edge).each { |edge| edge.vertices.each { |vertex| bounds.add(vertex.position) } }
            [bounds_record(entity, bounds, transform, inverse, path + [entity])]
          else
            []
          end
        end.compact
      end

      def bounds_record(entity, bounds, transform, inverse, path)
        return nil if bounds.empty?

        points = (0..7).map { |index| xyz(bounds.corner(index).transform(transform).transform(inverse)) }
        minimum = (0..2).map { |axis| points.map { |point| point[axis] }.min }
        maximum = (0..2).map { |axis| points.map { |point| point[axis] }.max }
        # 未分組的樑由 all_connected 合併 bounds；單一零厚度面則沒有體積。
        return nil if (0..2).any? { |axis| maximum[axis] - minimum[axis] < TOL }

        label = entity.respond_to?(:name) && !entity.name.empty? ? entity.name : '模型實體'
        { id: "#{label} ##{path.map(&:persistent_id).join('/')}", min: minimum, max: maximum }
      end

      def profile(model, selected, path, transform, start_vertex_id: nil, &choose_start)
        unless !selected.empty? && selected.all? { |entity| entity.is_a?(Sketchup::Edge) }
          raise InputError, '斷面模式請只選一條連通、無分叉、未閉合的正交折線。'
        end

        selector = if choose_start
                     lambda do |ends|
                       choices = ends.map do |vertex|
                         { id: vertex.persistent_id, point: xyz(vertex.position.transform(transform)) }
                       end
                       choose_start.call(choices)
                     end
                   end
        vertices = ordered_vertices(selected, start_vertex_id: start_vertex_id, &selector)
        points = vertices.map { |vertex| xyz(vertex.position.transform(transform)) }
        horizontal = points.each_cons(2).find { |a, b| (a[2] - b[2]).abs < TOL && Math.hypot(a[0] - b[0], a[1] - b[1]) > TOL }
        raise InputError, '單一直立邊未定義斷面平面；請選取同一垂直平面的完整折線。' unless horizontal

        xaxis = canonical_horizontal(sub(horizontal.last, horizontal.first))
        normal = [-xaxis[1], xaxis[0], 0.0]
        plane_offset = dot(points.first, normal)
        unless points.all? { |point| (dot(point, normal) - plane_offset).abs < TOL }
          raise InputError, '所選折線不在同一垂直平面，demo 未定義此情況。'
        end
        points.each_cons(2) do |a, b|
          delta = sub(b, a)
          vertical = Math.hypot(delta[0], delta[1]) < TOL
          level = delta[2].abs < TOL
          raise InputError, '斷面每段必須水平或垂直，不接受斜邊。' unless vertical || level
        end

        contacts = [points.first, points.last].map { |point| rc_contacts(model, point, xaxis, selected, path) }
        candidates = profile_frames(points, xaxis, normal, plane_offset, contacts)
        if candidates.empty?
          raise InputError, '兩端必須貼住可辨識的既有樓板底／牆面；無法從選取推定 demo 的 RC 基準。請檢查接面，其他封閉方式待使用者決定。'
        end
        if candidates.length > 1
          raise InputError, '端點同時接到多組不同的 RC 基準，無法唯一判定樓板／牆；此情況待使用者決定。'
        end

        chosen = candidates.first
        {
          input: { points: clean(chosen[:points]), source: "正交斷面（#{selected.length} 條邊）",
                   reference: chosen[:reference], source_path: path.map(&:persistent_id),
                   source_ids: selected.map(&:persistent_id), start_vertex_id: vertices.first.persistent_id,
                   start_point_mm: points.first,
                   axis_note: 'u 向遠離牆、v 向下；拉伸 L 沿 u 左側的水平法向。RC 僅驗證既有面接觸，未判定材料。' },
          frame: chosen[:frame], obstacles: []
        }
      end

      def ordered_vertices(edges, start_vertex_id: nil)
        adjacency = Hash.new { |hash, key| hash[key] = [] }
        edges.each { |edge| edge.vertices.each { |vertex| adjacency[vertex] << edge } }
        ends = adjacency.select { |_vertex, connected| connected.length == 1 }.keys
        unless ends.length == 2 && adjacency.values.all? { |connected| connected.length <= 2 }
          raise InputError, '折線必須有兩個端點且沒有分叉或閉環。'
        end

        if start_vertex_id.nil?
          raise StartPointError, '斷面起點會影響面材搭接；請先明示選擇折線的起點，不能由選取順序或實體 ID 推定。' unless block_given?

          start_vertex_id = yield(ends)
          raise StartPointError, '已取消斷面起點選擇，未建立任何構件。' if start_vertex_id.nil?
        end
        current = ends.find { |vertex| vertex.persistent_id == start_vertex_id }
        unless current
          raise StartPointError, '指定起點已不是目前折線的端點，請重新檢查並選擇起點。'
        end
        result = [current]
        visited = []
        loop do
          edge = adjacency[current].find { |candidate| !visited.include?(candidate) }
          break unless edge

          visited << edge
          current = (edge.vertices - [current]).first
          result << current
        end
        raise InputError, '所選邊含有第二條不連通折線。' unless visited.length == edges.length

        result
      end

      def each_face(entities, transform = Geom::Transformation.new, path = [], &block)
        entities.each do |entity|
          if entity.is_a?(Sketchup::Face)
            block.call(entity, transform, path)
          elsif container?(entity)
            each_face(entities_of(entity), transform * entity.transformation, path + [entity], &block)
          end
        end
      end

      def rc_contacts(model, world_point, xaxis, selected, selected_path)
        result = []
        each_face(model.entities) do |face, transform, path|
          next if path == selected_path && face.edges.all? { |edge| selected.include?(edge) }

          local = Geom::Point3d.new(world_point.map(&:mm)).transform(transform.inverse)
          classification = face.classify_point(local)
          next unless [Sketchup::Face::PointInside, Sketchup::Face::PointOnEdge, Sketchup::Face::PointOnVertex].include?(classification)

          world = face.outer_loop.vertices.map { |vertex| xyz(vertex.position.transform(transform)) }
          if world.all? { |point| (point[2] - world_point[2]).abs < TOL }
            result << { type: 'slab', value: world_point[2] }
          elsif world.all? { |point| (dot(point, xaxis) - dot(world_point, xaxis)).abs < TOL }
            result << { type: 'wall', value: dot(world_point, xaxis) }
          end
        end
        result.uniq { |contact| [contact[:type], contact[:value].round(5)] }
      end

      def profile_frames(points, xaxis, normal, plane_offset, contacts)
        candidates = []
        contacts.first.product(contacts.last).each do |first, last|
          slabs = [first, last].select { |contact| contact[:type] == 'slab' }.map { |contact| contact[:value] }.uniq
          walls = [first, last].select { |contact| contact[:type] == 'wall' }.map { |contact| contact[:value] }.uniq
          next if slabs.length > 1 || walls.length > 1

          directions = walls.empty? ? [1] : [1, -1]
          directions.each do |sign|
            uaxis = xaxis.map { |value| value * sign }
            uvalues = points.map { |point| dot(point, uaxis) }
            # 未存在的 RC 軸只作座標平移，最小值 1，避免被 onRC 誤認為接面。
            u0 = walls.empty? ? uvalues.min - 1.0 : walls.first * sign
            z0 = slabs.empty? ? points.map(&:last).max + 1.0 : slabs.first
            projected = snap_axes(points.map { |point| [dot(point, uaxis) - u0, z0 - point[2]] })
            next unless projected.all? { |u, v| u >= -TOL && v >= -TOL }

            origin = (0..2).map { |axis| uaxis[axis] * u0 + normal[axis] * plane_offset }
            origin[2] = z0
            laxis = [-uaxis[1], uaxis[0], 0.0]
            candidates << { points: projected, frame: transform_for(origin, uaxis, laxis),
                            reference: { wall: !walls.empty?, slab: !slabs.empty?,
                                         note: '只有實際接觸的 RC 基準有物理意義；未使用軸可任意平移。' } }
          end
        end
        candidates.uniq { |candidate| candidate[:points] }
      end

      # 同一軸線經世界座標旋轉／轉回時會有浮點漂移。將 TOL 內同軸值
      # 聚成完全相同的數值，再交給 core 的精確正交判斷；不吸附真正斜邊。
      def snap_axes(points)
        maps = (0..1).map do |axis|
          groups = []
          points.map { |point| point[axis] }.uniq.sort.each do |value|
            if groups.empty? || value - groups.last.first > TOL
              groups << [value]
            else
              groups.last << value
            end
          end
          groups.each_with_object({}) do |group, mapping|
            representative = group.any? { |value| value.abs < TOL } ? 0.0 : (group.sum / group.length).round(6)
            group.each { |value| mapping[value] = representative }
          end
        end
        points.map { |point| [maps[0].fetch(point[0]), maps[1].fetch(point[1])] }
      end

      # 對應 demo pfClean；平面邊界也合併 SketchUp 拆碎的共線邊。
      def clean(points, closed: false)
        result = points.each_with_object([]) { |point, output| output << point unless output.last == point }
        changed = true
        while changed && result.length > (closed ? 3 : 2)
          changed = false
          indices = closed ? (0...result.length) : (1...(result.length - 1))
          indices.each do |index|
            a = result[(index - 1) % result.length]
            b = result[index]
            c = result[(index + 1) % result.length]
            next unless (a[0] == b[0] && b[0] == c[0]) || (a[1] == b[1] && b[1] == c[1])

            result.delete_at(index)
            changed = true
            break
          end
        end
        result
      end
    end
  end
end
