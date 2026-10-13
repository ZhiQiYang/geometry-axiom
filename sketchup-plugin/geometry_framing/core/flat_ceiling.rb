# frozen_string_literal: true

require_relative 'geometry'
require_relative 'panel_axis'
require_relative 'checks'

module GeometryFraming
  module Core
    module FlatCeiling
      DEFAULTS = { pw: 915, pl: 1830, gap: 2, longY: true, corner: 'tl', cap: 450,
                   tw: 27, bear: 8, colEdge: true, ceil: 2500, bt: 6, md: 33 }.freeze
      BOARD_THICKNESS = 6
      MEMBER_HEIGHT = 33
      CORNERS = { 'tl' => '左上', 'tr' => '右上', 'bl' => '左下', 'br' => '右下' }.freeze
      module_function

      def build(rings:, params: {}, obstacles: [], id: 'F')
        Geometry.orthogonal_rings!(rings)
        rings = rings.map { |r| r.map(&:dup) }
        bb = Geometry.bbox(rings)
        p = DEFAULTS.merge(longY: bb[3] - bb[1] <= bb[2] - bb[0]).merge(params.transform_keys(&:to_sym))
        validate_params!(p)
        a = p[:longY] ? 'x' : 'y'
        b = p[:longY] ? 'y' : 'x'
        la = PanelAxis.build(span(bb, a), p[:pw], p[:gap], p[:tw])
        lb = PanelAxis.build(span(bb, b), p[:pl], p[:gap], p[:tw])
        po = a == 'x' ? 'v' : 'h'
        so = a == 'x' ? 'h' : 'v'
        members = wall_members(rings, p, po, id)
        clashes = primary_clashes(rings, p)
        pri = []
        la[:seams].each_with_index do |c, k|
          pos = world(bb, p, a, c)
          clash = clashes.include?(k)
          Geometry.interior(rings, po, pos).each do |lo, hi|
            src = "[D10a] 第 #{k + 1} 道板長邊縫(距起鋪牆 #{r1(c)})下要有支撐 → 主支壓在縫上,整支連續、不可斷開"
            src += ';收邊太窄,這道縫已往內挪(模板提案)' if la[:moved] && k == la[:seams].length - 1
            src += "\n⚠ 這道縫上的主支會碰到獨立柱或柱邊料:主支不能斷開,這個排板不成立 → 改起鋪角、板長方向或偏移" if clash
            member = { id: "#{id}-P#{pri.length + 1}", role: 'pri', pos: pos, orient: po,
                       s0: lo, s1: hi, len: hi - lo, clash: clash, src: src,
                       ends: clash ? '⚠ 碰到獨立柱或柱邊料(不允許)' : '兩端坐在牆邊的邊界材上' }
            members << member
            pri << member
          end
        end
        n_full = [1, (lb[:T].to_f / p[:cap] - 1e-9).ceil].max
        mod = lb[:T].to_f / n_full
        base = p[:pl] + (p[:gap] / 2.0).floor - lb[:T]
        lines = []
        m = 1
        while base + m * mod < lb[:D] - 1e-6
          t = (base + m * mod + 1e-6).floor
          if t.positive?
            src = "[模板] 間距上限 #{p[:cap]} → 一個完整格(#{p[:pl]} + #{p[:gap]} = #{lb[:T]})分 #{n_full} 段,模數 #{r1(mod)};主支上從縫中心線起取整數 mm 畫記號,這支副支照第 #{m} 個記號接"
            src += "(正好落在第 #{m / n_full} 道板端縫)" if (m % n_full).zero?
            lines << { t: t, kind: 'mark', src: src }
          end
          m += 1
        end
        mark_moved = nil
        unless lines.empty?
          limit = (lb[:D] - 1.5 * p[:tw]).floor
          if lines.last[:t] > limit + 1e-9
            mark_moved = { from: lines.last[:t], to: limit }
            lines.last[:t] = limit
            lines.last[:src] += ";離對牆太近,這個記號往內挪到距對牆 #{1.5 * p[:tw]}"
          end
        end
        seam_info = seam_support(lb, p, lines)
        lines.sort_by! { |line| line[:t] }
        sec = 0
        lines.each do |line|
          pos = world(bb, p, b, line[:t])
          Geometry.interior(rings, so, pos).each do |lo, hi|
            support = pri.select do |q|
              pos > q[:s0] + 1e-6 && pos < q[:s1] - 1e-6 && q[:pos] > lo + 1e-6 && q[:pos] < hi - 1e-6
            end.map { |q| q[:pos] }.uniq.sort
            [lo, *support, hi].each_cons(2) do |s0, s1|
              names = [s0, s1].map { |v| (v - lo).abs < 1e-6 || (v - hi).abs < 1e-6 ? '沿邊料' : '主支側面' }
              sec += 1
              members << { id: "#{id}-S#{sec}", role: 'sec', kind: line[:kind], pos: pos, orient: so,
                           s0: s0, s1: s1, len: s1 - s0, src: line[:src], ends: names.join(' → ') }
            end
          end
        end
        result = { id: id, rings: rings, bb: bb, A: a, B: b, la: la, lb: lb,
                   nFull: n_full, mod: mod, lines: lines, markMoved: mark_moved,
                   seamInfo: seam_info, pO: po, sO: so, members: members, params: p,
                   clashes: clashes, options: clash_free_options(rings, p) }
        result[:obstacles] = obstacle_diagnostics(rings, p, obstacles)
        result[:suggested_ceil] = result[:obstacles].select { |o| o[:hit] }.map { |o| o[:suggested_ceil] }.min
        result[:checks] = Checks.flat_ceiling(result)
        result[:valid] = result[:checks].all? { |c| c[:ok] }
        result[:solids] = solids(result)
        result
      end

      def validate_params!(p)
        %i[pw pl cap tw bt md].each do |key|
          raise ArgumentError, "#{key} 必須是正毫米值。" unless p[key].is_a?(Numeric) && p[key].finite? && p[key].positive?
        end
        %i[gap bear].each do |key|
          raise ArgumentError, "#{key} 必須是非負毫米值。" unless p[key].is_a?(Numeric) && p[key].finite? && p[key] >= 0
        end
        raise ArgumentError, '完成面高度必須是有限的毫米值。' unless p[:ceil].is_a?(Numeric) && p[:ceil].finite?
        raise ArgumentError, '起鋪角必須是 tl、tr、bl 或 br。' unless CORNERS.key?(p[:corner])
        %i[longY colEdge].each do |key|
          raise ArgumentError, "#{key} 必須是 true 或 false。" unless [true, false].include?(p[key])
        end
      end

      def span(bb, axis)
        axis == 'x' ? bb[2] - bb[0] : bb[3] - bb[1]
      end

      def world(bb, p, axis, distance)
        if axis == 'x'
          %w[tl bl].include?(p[:corner]) ? bb[0] + distance : bb[2] - distance
        else
          %w[tl tr].include?(p[:corner]) ? bb[1] + distance : bb[3] - distance
        end
      end

      def wall_members(rings, p, po, id)
        out = []
        rings.each_with_index do |ring, ri|
          # MUTATION: column_edge — 柱子四周沿邊料規則。
          next if ri.positive? && !p[:colEdge]

          ring.each_with_index do |a, i|
            b = ring[(i + 1) % ring.length]
            length = Math.hypot(b[0] - a[0], b[1] - a[1])
            mx = (a[0] + b[0]) / 2.0
            my = (a[1] + b[1]) / 2.0
            nx = (b[1] - a[1]) / length
            ny = -(b[0] - a[0]) / length
            sign = Geometry.inside?(rings, mx + nx * p[:tw], my + ny * p[:tw]) ? 1 : -1
            eo = a[1] == b[1] ? 'h' : 'v'
            parallel = eo == po
            label = if ri.positive?
                      '柱邊料(角色須宣告 primary 或 secondary,I21)'
                    elsif parallel
                      '邊界主支(primary;與主支平行的外邊,I21)'
                    else
                      '邊界材(boundary;與主支垂直的外邊,I20)'
                    end
            src = if ri.zero?
                    '板被牆切斷的邊要有支撐;其他角材的端面也要頂在它上面,不能直接頂 RC 牆'
                  else
                    '柱子四周要有沿邊料:主支、副支的端面要頂到角材才能固定,不能直接頂 RC 柱'
                  end
            out << { id: "#{id}-E#{out.length + 1}", role: 'wall', ri: ri, ei: i, eo: eo,
                     par: parallel, a: a, b: b, off: [nx * sign * p[:tw] / 2.0, ny * sign * p[:tw] / 2.0],
                     len: length, label: label, src: src, ends: '沿邊界' }
          end
        end
        out
      end

      def primary_clashes(rings, p)
        bb = Geometry.bbox(rings)
        a = p[:longY] ? 'x' : 'y'
        layout = PanelAxis.build(span(bb, a), p[:pw], p[:gap], p[:tw])
        edge = p[:colEdge] ? p[:tw] : 0
        layout[:seams].each_index.select do |k|
          pos = world(bb, p, a, layout[:seams][k])
          rings.drop(1).any? do |hole|
            h = Geometry.bbox([hole])
            lo = (a == 'x' ? h[0] : h[1]) - edge
            hi = (a == 'x' ? h[2] : h[3]) + edge
            pos + p[:tw] / 2.0 > lo + 1e-6 && pos - p[:tw] / 2.0 < hi - 1e-6
          end
        end
      end

      def clash_free_options(rings, p)
        [true, false].flat_map do |long_y|
          CORNERS.filter_map do |corner, name|
            if primary_clashes(rings, p.merge(longY: long_y, corner: corner)).empty?
              { longY: long_y, corner: corner, label: "#{name}起鋪・板長沿 #{long_y ? 'Y' : 'X'}" }
            end
          end
        end
      end

      def seam_support(lb, p, lines)
        g0 = (p[:gap] / 2.0).floor
        g1 = p[:gap] - g0
        lb[:seams].each_with_index.map do |seam, j|
          best = lines.map do |line|
            t = line[:t]
            { t: t, b: [seam - g0 - (t - p[:tw] / 2.0), t + p[:tw] / 2.0 - (seam + g1)].min }
          end.max_by { |candidate| candidate[:b] }
          if best && best[:b] >= p[:bear] - 1e-9
            { j: j, s: seam, drift: best[:t] - seam, b: best[:b], extra: false }
          else
            lines.reject! { |line| (line[:t] - seam).abs < p[:tw] - 1e-9 }
            lines << { t: seam, kind: 'seam', src: "[模板] 第 #{j + 1} 道板端縫沒落在記號的副支上(承接不足 #{p[:bear]} mm),縫下另加一支" }
            { j: j, s: seam, drift: 0, b: p[:tw] / 2.0 - [g0, g1].max, extra: true, best: best }
          end
        end
      end

      def end_faces(result)
        walls = result[:members].select { |m| m[:role] == 'wall' }.map { |m| [m[:ri], m[:ei]] }
        pri = result[:members].select { |m| m[:role] == 'pri' }
        bad = []
        result[:members].reject { |m| m[:role] == 'wall' }.each do |member|
          [member[:s0], member[:s1]].each do |ending|
            next if member[:role] == 'sec' && pri.any? { |q| (q[:pos] - ending).abs < 1e-6 && member[:pos] > q[:s0] - 1e-6 && member[:pos] < q[:s1] + 1e-6 }

            hit = nil
            result[:rings].each_with_index do |ring, ri|
              ring.each_with_index do |a, i|
                next if hit

                b = ring[(i + 1) % ring.length]
                if member[:orient] == 'h'
                  hit = [ri, i] if a[0] == b[0] && (a[0] - ending).abs < 1e-6 && member[:pos] >= [a[1], b[1]].min - 1e-6 && member[:pos] <= [a[1], b[1]].max + 1e-6
                else
                  hit = [ri, i] if a[1] == b[1] && (a[1] - ending).abs < 1e-6 && member[:pos] >= [a[0], b[0]].min - 1e-6 && member[:pos] <= [a[0], b[0]].max + 1e-6
                end
              end
            end
            bad << { m: member, e: ending, col: hit && hit[0].positive? } unless hit && walls.include?(hit)
          end
        end
        bad
      end

      def obstacle_diagnostics(rings, p, obstacles)
        top = p[:ceil] + p[:bt] + p[:md]
        obstacles.filter_map do |obstacle|
          obstacle = obstacle.transform_keys(&:to_sym)
          lo, hi = obstacle.values_at(:min, :max)
          unless [lo, hi].all? { |v| v.is_a?(Array) && v.length == 3 && v.all? { |n| n.is_a?(Numeric) && n.finite? } } && (0..2).all? { |i| hi[i] > lo[i] }
            raise ArgumentError, '障礙須提供 min/max 三維毫米包圍盒。'
          end
          next if Geometry.clip_cells(rings, lo[0], lo[1], hi[0], hi[1]).empty?

          # 符合 SKP 的完整高度帶：在完成面下方的物件不算上方 RC 樑。
          hit = lo[2] < top - 1e-6 && hi[2] > p[:ceil] + 1e-6
          { id: obstacle[:id], min: lo.dup, max: hi.dup, bottom: lo[2], top: top,
            hit: hit, suggested_ceil: lo[2] - p[:bt] - p[:md] }
        end
      end

      def member_rect(member, width)
        if member[:role] == 'wall'
          a, b, off = member.values_at(:a, :b, :off)
          x0 = [a[0], b[0]].min + off[0]
          x1 = [a[0], b[0]].max + off[0]
          y0 = [a[1], b[1]].min + off[1]
          y1 = [a[1], b[1]].max + off[1]
          a[1] == b[1] ? [x0, y0 - width / 2.0, x1, y0 + width / 2.0] : [x0 - width / 2.0, y0, x0 + width / 2.0, y1]
        elsif member[:orient] == 'h'
          [member[:s0], member[:pos] - width / 2.0, member[:s1], member[:pos] + width / 2.0]
        else
          [member[:pos] - width / 2.0, member[:s0], member[:pos] + width / 2.0, member[:s1]]
        end
      end

      def end_trim(result, member, value, width)
        if member[:role] == 'sec' && result[:members].any? { |q| q[:role] == 'pri' && (q[:pos] - value).abs < 1e-6 && member[:pos] > q[:s0] - 1e-6 && member[:pos] < q[:s1] + 1e-6 }
          return width / 2.0
        end
        result[:rings].drop(1).each do |hole|
          x0, y0, x1, y1 = Geometry.bbox([hole])
          on = if member[:orient] == 'h'
                 ((value - x0).abs < 1e-6 || (value - x1).abs < 1e-6) && member[:pos] >= y0 - 1e-6 && member[:pos] <= y1 + 1e-6
               else
                 ((value - y0).abs < 1e-6 || (value - y1).abs < 1e-6) && member[:pos] >= x0 - 1e-6 && member[:pos] <= x1 + 1e-6
               end
          return result[:params][:colEdge] ? width : 0 if on
        end
        width
      end

      def solids(result)
        p = result[:params]
        width = p[:tw]
        z = p[:ceil]
        out = []
        result[:la][:boards].each_with_index do |ta, i|
          result[:lb][:boards].each_with_index do |tb, j|
            av = ta.map { |t| world(result[:bb], p, result[:A], t) }.sort
            bv = tb.map { |t| world(result[:bb], p, result[:B], t) }.sort
            xv, yv = result[:A] == 'x' ? [av, bv] : [bv, av]
            cells = Geometry.clip_cells(result[:rings], xv[0], yv[0], xv[1], yv[1])
            next if cells.empty?

            boxes = cells.map { |x0, y0, x1, y1| [x0, y0, z, x1, y1, z + p[:bt]] }
            out << { id: "#{result[:id]}-B#{i + 1}-#{j + 1}", role: 'board', boxes: boxes,
                     rule: 'D10a：從起鋪牆整片排板，按房間與柱孔裁切。', section: [p[:pw], p[:bt]],
                     length: tb[1] - tb[0], full: result[:la][:full][i] && result[:lb][:full][j] }
          end
        end
        result[:members].each do |member|
          rect = member_rect(member, width)
          if member[:role] == 'wall'
            delta = member[:par] ? (member[:ri].zero? ? -width : width) : 0
            axis = member[:eo] == 'h' ? 0 : 1
            rect[axis] -= delta
            rect[axis + 2] += delta
          else
            axis = member[:orient] == 'h' ? 0 : 1
            rect[axis] += end_trim(result, member, member[:s0], width)
            rect[axis + 2] -= end_trim(result, member, member[:s1], width)
          end
          next unless rect[2] - rect[0] > 0.01 && rect[3] - rect[1] > 0.01

          axis = (member[:role] == 'wall' ? member[:eo] : member[:orient]) == 'h' ? 0 : 1
          out << { id: member[:id], role: member[:role], boxes: [[rect[0], rect[1], z + p[:bt], rect[2], rect[3], z + p[:bt] + p[:md]]],
                   rule: member[:src], section: [width, p[:md]], length: rect[axis + 2] - rect[axis] }
        end
        out
      end

      def r1(value)
        rounded = (value * 10).round / 10.0
        rounded == rounded.to_i ? rounded.to_i : rounded
      end
    end
  end
end
