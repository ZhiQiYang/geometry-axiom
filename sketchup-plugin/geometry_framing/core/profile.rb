# frozen_string_literal: true

# 斷面座標：u 向右、v 向下，單位 mm；u=0 為牆、v=0 為樓板底。
# 逐式移植已確認 demo 的 pfRing、pfModel、pfChecks、pf3D。
module GeometryFraming
  module Core
    module Profile
      DEFAULTS = { t: 6, a: 27, b: 33, L: 2400, cap: 450, flip: false }.freeze
      PRESETS = {
        cove: [[467, 0], [467, 148], [743, 148], [743, 351], [0, 351]].map(&:freeze).freeze,
        drop: [[600, 0], [600, 300], [0, 300]].map(&:freeze).freeze
      }.freeze

      module_function

      def build(points:, params: {})
        p = resolved_params(params)
        points = validated_points(points)
        ring = profile_ring(points)
        model = { mode: 'profile', params: p, points: points, ring: ring,
                  boards: [], longs: [], ribs: [], segs: [], errors: [] }
        make_segments(model)
        make_members(model) unless model[:segs].empty?
        model[:checks] = checks(model)
        model[:valid] = model[:checks].all? { |item| item[:ok] }
        model[:solids] = solids(model)
        model
      end

      def resolved_params(params)
        p = DEFAULTS.merge(params.transform_keys(&:to_sym))
        %i[t a b L cap].each do |key|
          value = Float(p[key])
          raise ArgumentError, "斷面參數 #{key} 必須為有限正數（mm）" unless value.finite? && value.positive?

          p[key] = value
        rescue TypeError, ArgumentError
          raise ArgumentError, "斷面參數 #{key} 必須為有限正數（mm）"
        end
        raise ArgumentError, '結構換邊 flip 必須為 true 或 false' unless [true, false].include?(p[:flip])

        p
      end

      def validated_points(points)
        raise ArgumentError, '完成面至少需要兩個斷面座標點' unless points.is_a?(Array) && points.length >= 2

        points.map do |point|
          raise ArgumentError, '斷面座標必須是 [u, v]，單位 mm' unless point.is_a?(Array) && point.length == 2

          point.map do |coordinate|
            value = Float(coordinate)
            raise ArgumentError, '斷面座標必須是有限數字（mm）' unless value.finite?

            value
          rescue TypeError, ArgumentError
            raise ArgumentError, '斷面座標必須是有限數字（mm）'
          end
        end
      end

      def profile_ring(points)
        ring = points.map(&:dup)
        first = points.first
        last = points.last
        if (on_wall?(last) && on_slab?(first)) || (on_slab?(last) && on_wall?(first))
          ring << [0, 0]
        end
        ring
      end

      def make_segments(model)
        model[:points].each_cons(2).with_index do |(from, to), index|
          du = to[0] <=> from[0]
          dv = to[1] <=> from[1]
          if du != 0 && dv != 0
            model[:errors] << "第 #{index + 1} 段不是水平或垂直"
            next
          end
          next if du.zero? && dv.zero?

          length = (to[0] - from[0]).abs + (to[1] - from[1]).abs
          mid = [(from[0] + to[0]) / 2.0, (from[1] + to[1]) / 2.0]
          normal = [-dv, du]
          normal = [dv, -du] unless inside?(model[:ring], mid[0] + normal[0] * 2, mid[1] + normal[1] * 2)
          normal = normal.map { |component| -component } if model[:params][:flip]
          model[:segs] << { p: from, q: to, d: [du, dv], n: normal, len: length }
        end
      end

      def make_members(model)
        p = model[:params]
        t = p[:t]
        segments = model[:segs]
        count = segments.length
        segments.each_with_index do |segment, k|
          s0 = k.positive? && corner(segments, k) == :convex ? t : 0
          s1 = segment[:len]
          if k < count - 1 && corner(segments, k + 1) == :reflex
            s1 += t + size(segment[:d], p)
          end
          model[:boards] << { seg: k, r: rectangle(segment, s0, s1, 0, t),
                              src: "第 #{k + 1} 段完成面的面材(厚 #{number(t)})" }
        end

        model[:longs] << { r: member(segments.first, 0, size(segments.first[:d], p), p),
                           src: '起點:完成面接到 RC 的那一端' }
        (1...count).each do |k|
          before = segments[k - 1]
          after = segments[k]
          case corner(segments, k)
          when :convex
            cu = after[:p][0] + t * (before[:n][0] + after[:n][0])
            cv = after[:p][1] + t * (before[:n][1] + after[:n][1])
            nu = before[:n][0].zero? ? after[:n][0] : before[:n][0]
            nv = before[:n][1].zero? ? after[:n][1] : before[:n][1]
            rect = [nu.positive? ? cu : cu - p[:a], nv.positive? ? cv : cv - p[:b],
                    nu.positive? ? cu + p[:a] : cu, nv.positive? ? cv + p[:b] : cv]
            model[:longs] << { r: rect, src: "第 #{k} 個轉角(凸角):一支同時托兩塊面材" }
          when :reflex
            model[:longs] << { r: member(before, before[:len] + t, before[:len] + t + size(before[:d], p), p),
                               src: "第 #{k} 個轉角(凹角):托前一段面材的端部" }
            model[:longs] << { r: member(after, 0, size(after[:d], p), p),
                               src: "第 #{k} 個轉角(凹角):托後一段面材的起點" }
          end
        end
        last = segments.last
        model[:longs] << { r: member(last, last[:len] - size(last[:d], p), last[:len], p),
                           src: '終點:完成面接到 RC 的那一端' }

        segments.each_with_index do |segment, k|
          s0 = if k.zero?
                 size(segment[:d], p)
               elsif corner(segments, k) == :convex
                 t + size(segment[:d], p)
               elsif corner(segments, k) == :reflex
                 size(segment[:d], p)
               else
                 0
               end
          s1 = if k == count - 1
                 segment[:len] - size(segment[:d], p)
               elsif corner(segments, k + 1) == :convex
                 segment[:len] - t - size(segment[:d], p)
               elsif corner(segments, k + 1) == :reflex
                 segment[:len] + t
               else
                 segment[:len]
               end
          next unless s1 - s0 > 0.5

          model[:ribs] << { seg: k, r: member(segment, s0, s1, p),
                            src: "第 #{k + 1} 段的橫撐:接在兩端縱向料之間,托面材" }
        end
      end

      def size(direction, params)
        direction[0].zero? ? params[:b] : params[:a]
      end

      def corner(segments, index)
        before = segments[index - 1]
        after = segments[index]
        return :convex if after[:d] == before[:n]
        return :reflex if after[:d] == before[:n].map { |value| -value }

        :straight
      end

      def rectangle(segment, s0, s1, c0, c1)
        corners = [s0, s1].product([c0, c1]).map do |s, c|
          [segment[:p][0] + segment[:d][0] * s + segment[:n][0] * c,
           segment[:p][1] + segment[:d][1] * s + segment[:n][1] * c]
        end
        [corners.map(&:first).min, corners.map(&:last).min,
         corners.map(&:first).max, corners.map(&:last).max]
      end

      def member(segment, s0, s1, params)
        rectangle(segment, s0, s1, params[:t], params[:t] + size(segment[:n], params))
      end

      def checks(model)
        p = model[:params]
        points = model[:points]
        errors = model[:errors]
        rows = [1, (p[:L] / p[:cap] - 1e-9).ceil].max
        spacing = p[:L] / rows
        out = []
        add_check(out, :profile_orthogonal, errors.empty? && !model[:segs].empty?,
                  '完成面每段都是水平或垂直(D35 正交)',
                  errors.empty? ? "#{model[:segs].length} 段" : errors.join("\n"))
        add_check(out, :profile_rc, on_rc?(points.first) && on_rc?(points.last),
                  '完成面兩端接到 RC,骨架有東西可固定', "起點#{where(points.first)}、終點#{where(points.last)}")
        add_check(out, :profile_boards, true, '每段完成面內側都有面材', "#{model[:boards].length} 塊,厚 #{number(p[:t])}")
        add_check(out, :profile_longs, true, '每個轉角與兩端都有縱向料托住板邊', "#{model[:longs].length} 支,沿 L 連續")
        add_check(out, :profile_spacing, spacing <= p[:cap] + 1e-6, "橫撐沿 L 的間距 ≤ #{number(p[:cap])}",
                  "L #{number(p[:L])} 分 #{rows} 段,間距 #{number(spacing.round(1))};每個位置 #{model[:ribs].length} 支,共 #{model[:ribs].length * (rows + 1)} 支")
        all = model[:boards].map { |item| item.merge(kind: '面材') } +
              model[:longs].map { |item| item.merge(kind: '縱向料') } +
              model[:ribs].map { |item| item.merge(kind: '橫撐') }
        outside = all.reject { |item| rectangle_inside?(item[:r], model[:ring]) }
        detail = outside.empty? ? '是' : "#{outside.length} 件超出:#{outside.map { |item| item[:kind] }.uniq.join('、')}(某段太短或結構換錯邊)"
        add_check(out, :profile_inside, outside.empty?, '構件都在斷面輪廓內(D35)', detail)
        overlaps = []
        all.combination(2) do |first, second|
          a = first[:r]
          b = second[:r]
          next unless [a[2], b[2]].min - [a[0], b[0]].max > 0.5 &&
                      [a[3], b[3]].min - [a[1], b[1]].max > 0.5

          overlaps << "#{first[:kind]}/#{second[:kind]}"
        end
        detail = overlaps.empty? ? '是' : "#{overlaps.length} 處:#{overlaps.first(3).join('、')}#{overlaps.length > 3 ? ' …' : ''}(某段比兩端的料還短)"
        add_check(out, :profile_overlap, overlaps.empty?, '構件互不重疊(D36)', detail)
        short = model[:segs].each_with_index.select { |segment, _index| segment[:len] < 2 * [p[:a], p[:b]].max + 2 * p[:t] }
        unless short.empty?
          add_check(out, :profile_short, true, '很短的段', short.map do |segment, index|
            "第 #{index + 1} 段只有 #{number(segment[:len])} mm,兩端的料幾乎接在一起,不需要橫撐"
          end.join("\n"))
        end
        out
      end

      def add_check(output, id, ok, title, detail)
        output << { id: id, ok: ok, title: title, detail: detail }
      end

      def rectangle_inside?(rect, ring)
        e = 0.5
        points = [[rect[0] + e, rect[1] + e], [rect[2] - e, rect[1] + e],
                  [rect[0] + e, rect[3] - e], [rect[2] - e, rect[3] - e],
                  [(rect[0] + rect[2]) / 2.0, (rect[1] + rect[3]) / 2.0]]
        points.all? { |u, v| inside?(ring, u, v) }
      end

      def inside?(ring, u, v)
        hit = false
        ring.each_with_index do |(xi, yi), index|
          xj, yj = ring[index - 1]
          hit = !hit if (yi > v) != (yj > v) && u < (xj - xi) * (v - yi) / (yj - yi) + xi
        end
        hit
      end

      def on_wall?(point)
        point[0].abs < 1e-6
      end

      def on_slab?(point)
        point[1].abs < 1e-6
      end

      def on_rc?(point)
        on_wall?(point) || on_slab?(point)
      end

      def where(point)
        return '在樓板上' if on_slab?(point)
        return '在牆上' if on_wall?(point)

        '懸空'
      end

      def number(value)
        value == value.to_i ? value.to_i.to_s : value.to_s
      end

      # pf3D 的 n+1 排（含兩端），首末排依材寬向 L 內縮。
      # 每個 box 使用 [x0,y0,z0,x1,y1,z1]；x=u、y=L 正向、z=-v。
      def solids(model)
        p = model[:params]
        output = []
        { boards: 'board', longs: 'long' }.each do |key, role|
          model[key].each_with_index do |item, index|
            rect = item[:r]
            output << solid("#{role}-#{index + 1}", role, item, 0, p[:L],
                            [rect[2] - rect[0], rect[3] - rect[1]], p[:L])
          end
        end
        n = [1, (p[:L] / p[:cap] - 1e-9).ceil].max
        width = [p[:a], p[:b]].min
        (0..n).each do |row|
          w0 = [0, [p[:L] - width, row * p[:L] / n - width / 2.0].min].max
          model[:ribs].each_with_index do |item, index|
            segment = model[:segs][item[:seg]]
            rect = item[:r]
            length = segment[:d][0].zero? ? rect[3] - rect[1] : rect[2] - rect[0]
            output << solid("rib-#{row + 1}-#{index + 1}", 'rib', item, w0, w0 + width,
                            [size(segment[:n], p), width], length)
          end
        end
        # Demo box3 不畫任一方向厚度 <= 0.01 mm 的退化實體。
        output.reject do |item|
          box = item[:boxes].first
          (0..2).any? { |axis| box[axis + 3] - box[axis] <= 0.01 }
        end
      end

      def solid(id, role, item, from, to, section, length)
        rect = item[:r]
        { id: id, role: role, boxes: [[rect[0], from, -rect[3], rect[2], to, -rect[1]]],
          rule: item[:src], section: section, length: length, src: item[:src] }
      end
    end
  end
end
