# frozen_string_literal: true

module GeometryFraming
  module Core
    module PanelAxis
      module_function

      # D10a：從起鋪牆整片排板；縫與收邊完全移植確認版 demo。
      def build(d, p, gap, tw)
        unless [d, p, tw].all? { |v| v.is_a?(Numeric) && v.finite? && v.positive? } &&
               gap.is_a?(Numeric) && gap.finite? && gap >= 0
          raise ArgumentError, '排板尺寸與角材寬須為正毫米值，板縫不得為負。'
        end
        period = p + gap
        g0 = (gap / 2.0).floor
        g1 = gap - g0
        seams = []
        k = 0
        while (k + 1) * period < d - 1e-9
          seams << k * period + p + g0
          k += 1
        end
        moved = nil
        limit = (d - 1.5 * tw).floor
        # MUTATION: edge_shift — 收邊挪縫規則。
        if !seams.empty? && seams.last > limit + 1e-9
          moved = { from: seams.last, to: limit }
          seams[-1] = limit
        end
        boards = []
        t0 = 0
        seams.each do |seam|
          boards << [t0, seam - g0]
          t0 = seam + g1
        end
        boards << [t0, [d, t0 + p].min]
        { D: d, P: p, T: period, seams: seams, boards: boards,
          full: boards.map { |a, b| b - a >= p - 0.5 }, moved: moved }
      end
    end
  end
end
