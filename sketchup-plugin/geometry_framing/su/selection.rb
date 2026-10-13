# frozen_string_literal: true

require_relative 'obstacles'

module GeometryFraming
  module SU
    class InputError < StandardError; end
    class StartPointError < InputError; end

    # active_entities 內讀到的位置已是世界座標；唯讀查詢不能切換 active_path，
    # 否則光按「檢查」就會新增 Undo 紀錄或清掉 Redo。
    # 寫入根層才暫離編輯；呼叫者必須把離開、寫入、還原包在同一 operation。
    module Context
      module_function

      # 官方 ModelObserver#onActivePathChanged 說明編輯中的幾何讀值為世界座標。
      # 根層／其他 instance 遞迴則沿其 API 回傳的 transformation 累積。
      # https://ruby.sketchup.com/Sketchup/ModelObserver.html#onActivePathChanged-instance_method
      def read(model)
        selected = model.selection.to_a
        path = model.active_path || []
        yield(selected, path, Geom::Transformation.new)
      end

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
        Context.read(model) do |selected, path, transform| # UX_READ_WITHOUT_CONTEXT_SWITCH
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
        projection = project_flat_rings(world_rings)
        rings, z, origin, xaxis, yaxis = projection.values_at(:rings, :ceil, :origin, :xaxis, :yaxis)
        frame = transform_for(origin, xaxis, yaxis)
        obstacles = Obstacles.collect(model, selected_path: path, face: face, inverse: frame.inverse)
        {
          input: { rings: rings, ceil: z, source: "水平完成面 ##{face.persistent_id}",
                   axis_note: '平面 X 沿外圈整數長度最長的有向邊；同長取外圈先出現者，Y 朝其右側。角名跟隨此局部座標。',
                   source_path: path.map(&:persistent_id), source_id: face.persistent_id },
          frame: frame, obstacles: obstacles
        }
      end

      # 純數值 world(mm) → 平面(mm)；flat() 與一般 Ruby 測試共用真正的投影。
      def project_flat_rings(world_rings)
        z = world_rings.first.first[2]
        unless world_rings.flatten(1).all? { |point| (point[2] - z).abs < TOL }
          raise InputError, '只接受世界座標中的水平面；斜面尚待使用者決定。'
        end

        edges = world_rings.first.each_with_index.map do |point, i|
          sub(world_rings.first[(i + 1) % world_rings.first.length], point)
        end
        # D1 的整數長度比較可避免等長邊因 API 浮點誤差輪流中選。
        # 同長保留 outer_loop 先者；保留有向邊而不朝世界紅軸翻號，
        # 因此同一個 loop 作剛體旋轉時，局部起鋪角仍指向同一個角落。
        longest = edges.max_by { |edge| Math.hypot(edge[0], edge[1]).round }
        xaxis = normalize([longest[0], longest[1], 0.0])
        yaxis = [xaxis[1], -xaxis[0], 0.0] # demo 的 Y 朝平面圖下方。
        projected = world_rings.map { |ring| ring.map { |point| [dot(point, xaxis), dot(point, yaxis)] } }
        minx = projected.flatten(1).map(&:first).min
        miny = projected.flatten(1).map(&:last).min
        rings = projected.map do |ring|
          integer_projection(ring.map { |x, y| [x - minx, y - miny] }, closed: true)
        end
        rings = rings.map { |ring| clean(ring, closed: true) }
        origin = xaxis.zip(yaxis).map { |x, y| x * minx + y * miny }
        { rings: rings, ceil: z.round, origin: origin, xaxis: xaxis, yaxis: yaxis }
      end

      def container?(entity)
        entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)
      end

      def entities_of(instance)
        instance.is_a?(Sketchup::Group) ? instance.entities : instance.definition.entities
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
            projected = integer_projection(points.map { |point| [dot(point, uaxis) - u0, z0 - point[2]] })
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

      # D1 只在原生輸入→局部平面邊界落到整數 mm；不取整 core 衍生的
      # 半寬、構件斷面或材長。先檢查未取整偏差，避免以取整掩蓋斜邊。
      def integer_projection(points, closed: false)
        segments = points.each_cons(2).to_a
        segments << [points.last, points.first] if closed
        if segments.any? { |a, b| [(a[0] - b[0]).abs, (a[1] - b[1]).abs].min > 0.5 }
          raise InputError, 'D1 整數 mm：取整前偏離正交超過 0.5 mm，不能把斜邊改成正交。'
        end

        rounded = points.map { |point| point.map { |value| value.round } } # D1_INTEGER_MM_PROJECTION
        segments = rounded.each_cons(2).to_a
        segments << [rounded.last, rounded.first] if closed
        unless segments.all? { |a, b| a[0] == b[0] || a[1] == b[1] }
          raise InputError, 'D1 整數 mm：取整後仍有非正交邊，請修正輸入。'
        end
        rounded
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
