# frozen_string_literal: true

module GeometryFraming
  module Core
    # 純毫米幾何；平面座標 x 向右、y 向下，與確認版 demo 相同。
    module Geometry
      EPS = 0.01
      module_function

      def bbox(rings)
        points = rings.flatten(1)
        [points.map(&:first).min, points.map(&:last).min,
         points.map(&:first).max, points.map(&:last).max]
      end

      def inside?(rings, x, y)
        odd = false
        rings.each do |ring|
          ring.each_with_index do |(xi, yi), i|
            xj, yj = ring[(i - 1) % ring.length]
            odd = !odd if (yi > y) != (yj > y) && x < (xj - xi) * (y - yi).to_f / (yj - yi) + xi
          end
        end
        odd
      end

      def crossings(rings, axis, c)
        points = []
        rings.each do |ring|
          ring.each_with_index do |a, i|
            b = ring[(i + 1) % ring.length]
            if axis == 'h' && a[0] == b[0]
              points << a[0] if c > [a[1], b[1]].min && c < [a[1], b[1]].max
            elsif axis == 'v' && a[1] == b[1]
              points << a[1] if c > [a[0], b[0]].min && c < [a[0], b[0]].max
            end
          end
        end
        points.sort.each_slice(2).select { |pair| pair.length == 2 }
      end

      def intersect_intervals(a, b)
        out = []
        i = j = 0
        while i < a.length && j < b.length
          lo = [a[i][0], b[j][0]].max
          hi = [a[i][1], b[j][1]].min
          out << [lo, hi] if hi - lo > 1e-6
          a[i][1] < b[j][1] ? i += 1 : j += 1
        end
        out
      end

      def interior(rings, axis, c)
        intersect_intervals(crossings(rings, axis, c - EPS), crossings(rings, axis, c + EPS))
      end

      # 矩形與可含孔的正交多邊形相交，依 demo 逐列合併。
      def clip_cells(rings, x0, y0, x1, y1)
        return [] unless x1 > x0 && y1 > y0

        xs = [x0, x1]
        ys = [y0, y1]
        rings.each do |ring|
          ring.each do |x, y|
            xs << x if x > x0 && x < x1
            ys << y if y > y0 && y < y1
          end
        end
        xs = xs.uniq.sort
        ys = ys.uniq.sort
        out = []
        ys.each_cons(2) do |ya, yb|
          run = nil
          xs.each_cons(2) do |xa, xb|
            if inside?(rings, (xa + xb) / 2.0, (ya + yb) / 2.0)
              run = xa if run.nil?
            elsif !run.nil?
              out << [run, ya, xa, yb]
              run = nil
            end
          end
          out << [run, ya, xs.last, yb] unless run.nil?
        end
        out
      end

      def orthogonal_rings!(rings)
        unless rings.is_a?(Array) && !rings.empty? && rings.all? { |r| r.is_a?(Array) && r.length >= 4 }
          raise ArgumentError, '平釘模式需要一個正交外圈，可另含柱孔內圈。'
        end
        rings.each do |ring|
          ring.each_with_index do |a, i|
            b = ring[(i + 1) % ring.length]
            unless a.is_a?(Array) && a.length == 2 && a.all? { |v| v.is_a?(Numeric) && v.finite? }
              raise ArgumentError, '平面座標必須是有限的毫米數值 [x, y]。'
            end
            next unless b.is_a?(Array) && b.length == 2

            if a == b || (a[0] != b[0] && a[1] != b[1])
              raise ArgumentError, '第一版只支援非零長度、水平或垂直的正交邊。'
            end
          end
        end
      end
    end
  end
end
