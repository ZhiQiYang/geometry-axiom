# frozen_string_literal: true

module GeometryFraming
  module Core
    module Checks
      module_function

      def entry(id, ok, title, detail)
        { id: id.to_s, ok: !!ok, title: title, detail: detail }
      end

      # 與確認版 demo check() 相同的八項；規則識別碼供 UI 與突變測試引用。
      def flat_ceiling(g)
        p = g[:params]
        la, lb = g.values_at(:la, :lb)
        width = p[:tw]
        start_full = lambda do |layout|
          count = layout[:boards].length - 1 - (layout[:moved] ? 1 : 0)
          layout[:full].first([count, 0].max).all?
        end
        remainder = lambda do |layout|
          board = layout[:boards].last
          layout[:full].last ? '剛好整片' : "對牆收邊 #{FlatCeiling.r1(board[1] - board[0])} mm"
        end
        out = [entry(:start_full, start_full.call(la) && start_full.call(lb),
                     '起鋪牆那側全是整片板,裁切只在對牆',
                     "915 向:整片 #{la[:full].count(true)} 排,#{remainder.call(la)}\n1830 向:整片 #{lb[:full].count(true)} 片,#{remainder.call(lb)}")]
        bad = FlatCeiling.end_faces(g)
        detail = if bad.empty?
                   '副支頂主支側面或沿邊料;主支兩端坐在牆邊的邊界材上'
                 else
                   "#{bad.length} 個端面直接頂到 RC#{bad.any? { |x| x[:col] } ? '柱' : '牆'}:#{bad.map { |x| x[:m][:id] }.uniq.first(6).join('、')}#{bad.length > 6 ? ' …' : ''}"
                 end
        out << entry(:end_faces, bad.empty?, '每個端面都頂在角材上,不直接頂 RC', detail)
        marks = g[:lines].map { |line| line[:t] }
        counts = lb[:boards].each_with_index.filter_map do |(b0, b1), j|
          marks.count { |t| t > b0 + width / 2.0 && t < b1 - width / 2.0 } if lb[:full][j]
        end
        out << entry(:equal_marks, counts.all? { |c| c == g[:nFull] - 1 },
                     "每個完整格(板+縫 #{lb[:T]}):中間 #{g[:nFull] - 1} 支,#{g[:nFull]} 段",
                     "等分數 = ⌈#{lb[:T]} ÷ 上限 #{p[:cap]}⌉ = #{g[:nFull]};模數 #{FlatCeiling.r1(g[:mod])},記號取整數 mm\n各整片板中間:#{counts.empty? ? '(無整片)' : counts.join('、')} 支")
        supports = [width / 2.0, *marks, lb[:D] - width / 2.0]
        worst = [0, *supports.each_cons(2).map { |a, b| b - a }].max
        inner = marks.each_cons(2).map { |a, b| FlatCeiling.r1(b - a) }.uniq.sort.first(4)
        good_spacing = worst <= p[:cap] + 1e-6
        out << entry(:spacing, good_spacing, "1830 向副支中心距 ≤ 間距上限 #{p[:cap]}",
                     "最大 #{FlatCeiling.r1(worst)} mm;記號之間 #{inner.empty? ? '—' : inner.join(' / ')} mm#{good_spacing ? '(取整差 1 mm,都在上限內)' : ''}")
        seam_detail = g[:seamInfo].map do |x|
          "第 #{x[:j] + 1} 道:" + if x[:extra]
                                 "記號的副支承接不足,縫下另加一支(承接 #{FlatCeiling.r1(x[:b])})"
                               else
                                 "記號與縫中心差 #{FlatCeiling.r1(x[:drift].abs)} mm,承接 #{FlatCeiling.r1(x[:b])} mm"
                               end
        end
        out << entry(:seam_bearing, g[:seamInfo].all? { |x| x[:b] >= p[:bear] - 1e-9 },
                     "板端縫落在副支上,兩側承接 ≥ #{p[:bear]} mm",
                     seam_detail.empty? ? '沒有板端縫(1830 向只有一片)' : seam_detail.join("\n"))
        # MUTATION: primary_continuity — 主支不可切斷；即使保留診斷段，也不能接受該排板。
        continuity_ok = g[:clashes].empty?
        continuity_detail = if continuity_ok
                              '每支主支從牆邊連續到對牆;副支裁成段,夾在主支之間'
                            else
                              choices = g[:options].map { |option| option[:label] }
                              "#{g[:clashes].length} 道主支線會碰到獨立柱或柱邊料,這個排板不成立。\n不衝突的選擇:#{choices.empty? ? '(沒有,需要偏移排板)' : choices.join('、')}"
                            end
        out << entry(:primary_continuity, continuity_ok, '主支整支連續、不可斷開(不碰獨立柱)', continuity_detail)
        obstacle_detail = g[:obstacles].map do |obstacle|
          "#{obstacle[:id]}:樑底 #{obstacle[:bottom]}、骨架頂 #{obstacle[:top]} → " + if obstacle[:hit]
            "骨架碰到樑,完成面要降到 ≤ #{obstacle[:suggested_ceil]}(貼樑底),或改包樑另作"
          else
            '與骨架高度帶無重疊'
          end
        end
        out << entry(:obstacles, g[:obstacles].none? { |obstacle| obstacle[:hit] }, '骨架不碰 RC 樑(主支不可切)',
                     obstacle_detail.empty? ? '這一面上方沒有樑' : obstacle_detail.join("\n"))
        moved = []
        moved << '915 向最後一道縫' if la[:moved]
        moved << '1830 向最後一道縫' if lb[:moved]
        moved << '最後一個記號' if g[:markMoved]
        out << entry(:edge_shift, true, '收邊太窄時往內挪',
                     moved.empty? ? '收邊寬度足夠,不需要挪' : "#{moved.join('、')}離對牆不到 #{1.5 * width},往內挪到距對牆 #{1.5 * width}")
        out
      end
    end
  end
end
